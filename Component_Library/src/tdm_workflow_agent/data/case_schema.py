"""Validated JSON contract for balanced TN/radial-DN/aggregate-MG data."""
from __future__ import annotations
import hashlib
import json
import math
from typing import Any, TypeAlias
from .indexing import network_index

CaseData: TypeAlias = dict[str, Any]
NetworkData: TypeAlias = dict[str, Any]
Branch: TypeAlias = dict[str, Any]
Device: TypeAlias = dict[str, Any]
Interface: TypeAlias = dict[str, Any]
Scenario: TypeAlias = dict[str, Any]


def hash_payload(payload: dict, excluded: tuple[str, ...] = ()) -> str:
    value = {k: v for k, v in payload.items() if k not in excluded}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def case_hash(case: dict) -> str:
    return hash_payload(case, ('system_hash',))


def _unique(records: list[dict], label: str) -> set:
    ids = [record['id'] for record in records]
    if any(v is None for v in ids) or len(ids) != len(set(ids)):
        raise ValueError(f'duplicate/missing {label} ID')
    return set(ids)


def _finite(value: Any, label: str) -> float:
    if not isinstance(value, (float, int)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f'nonfinite/non-numeric {label}')
    return value


def validate_case(case: CaseData) -> dict:
    """Validate actual structure and units without assuming a benchmark size.

    Hash verification belongs to load_case: callers can validate in-memory case
    edits before assigning their new content hash.
    """
    required = ('system_id', 'data_version', 'networks', 'devices', 'loads', 'interfaces',
                'profiles', 'time_grid', 'safety', 'source_manifest', 'capabilities')
    if any(key not in case for key in required):
        raise ValueError('missing canonical case fields')
    grid = case['time_grid']
    intervals = grid['intervals']
    if not intervals or len(set(intervals)) != len(intervals):
        raise ValueError('missing/duplicate time intervals')
    if _finite(grid['dt_hours'], 'dt_hours') <= 0:
        raise ValueError('dt_hours must be positive')
    ntime = len(intervals)
    units = case.get('units', {})
    for key, expected in [('p', 'MW'), ('q', 'MVAr'), ('energy', 'MWh')]:
        if key in units and units[key] != expected:
            raise ValueError(f'invalid units for {key}: expected {expected}')
    netids = _unique(case['networks'], 'network')
    _unique(case['devices'], 'resource')
    loadids = _unique(case['loads'], 'load')
    _unique(case['interfaces'], 'interface')
    mgids = _unique(case.get('microgrids', []), 'microgrid')
    bus_keys = set()
    networks = {n['id']: n for n in case['networks']}
    if sum(n['layer'] == 'TN' for n in case['networks']) != 1:
        raise ValueError('one TN is required')
    for network in case['networks']:
        if network['layer'] not in ('TN', 'DN') or network.get('phase_model') != 'balanced':
            raise ValueError('unsupported network layer/phase model')
        if _finite(network['base_mva'], 'base_mva') <= 0:
            raise ValueError('invalid network base MVA')
        network_index(network)
        for bus in network['buses']:
            bus_keys.add((network['id'], bus['id']))
            if _finite(bus['base_kv'], 'base_kv') <= 0 or not 0 < bus['v_min_pu'] <= bus['v_max_pu']:
                raise ValueError('invalid bus voltage/base bounds')
            for key in ('gs_mw', 'bs_mvar', 'vm_pu', 'va_degree'):
                if key in bus:
                    _finite(bus[key], key)
        for branch in network['branches']:
            for key in ('r_pu', 'x_pu', 'b_pu', 'tap', 'shift_degree'):
                _finite(branch[key], key)
            if branch['status'] and branch['r_pu'] == 0 and branch['x_pu'] == 0:
                raise ValueError('zero branch impedance')
            if branch['tap'] <= 0:
                raise ValueError('tap must be positive; convert MATPOWER zero marker to one')
            if branch['rate_mva'] is not None and _finite(branch['rate_mva'], 'rate_mva') <= 0:
                raise ValueError('finite branch rate must be positive, missing rate is null')
    profiles = case['profiles']
    renewable_profiles = {d.get('profile_id') for d in case['devices'] if d.get('kind') in ('PV', 'WT')}
    microgrids = {mg['id']: mg for mg in case.get('microgrids', [])}
    for pid, values in profiles.items():
        if len(values) != ntime:
            raise ValueError(f'{pid}: missing/extra profile time')
        for value in values:
            if _finite(value, pid) < 0:
                raise ValueError('negative profile')
            if (pid in renewable_profiles or pid.endswith('_CF') or pid in ('PVShape_pu', 'WTShape_pu')) and value > 1:
                raise ValueError(f'{pid}: CF > 1')
        if pid.endswith(':PV_CF') and 'PVShape_pu' in profiles:
            if any(base == 0 and value != 0 for base, value in zip(profiles['PVShape_pu'], values)):
                raise ValueError('PV nonzero during source night')
    for device in case['devices']:
        if device.get('kind') not in {'GEN', 'PV', 'WT', 'GT', 'BESS', 'SVC', 'FLEX'}:
            raise ValueError('unknown resource kind')
    for record in case['loads'] + case['devices']:
        if record['network_id'] not in netids:
            raise ValueError('unknown resource/load network')
        if record.get('kind') != 'FLEX' and (record['network_id'], record['bus_id']) not in bus_keys:
            raise ValueError('unknown resource/load bus')
        if record.get('owner_type') == 'MG' and record.get('owner_id') not in mgids:
            raise ValueError('unknown resource owner microgrid')
        if record.get('owner_type') == 'MG':
            mg = microgrids[record['owner_id']]
            if (record['network_id'], record['bus_id']) != (mg['parent_dn'], mg['pcc_bus']):
                raise ValueError('MG resource/load is not connected at owner PCC')
        for key in ('p_nameplate_mw', 's_rating_mva', 'e_nameplate_mwh', 'p_charge_max_mw', 'p_discharge_max_mw'):
            if key in record and _finite(record[key], key) < 0:
                raise ValueError('negative device capacity')
        if 'profile_id' in record and record['profile_id'] not in profiles:
            raise ValueError('unknown profile reference')
        for key, value in record.items():
            if key.endswith(('_mw', '_mvar', '_mwh', '_mva')):
                _finite(value, key)
        if record.get('kind') == 'FLEX':
            if not record['baseline_load_ids'] or not set(record['baseline_load_ids']) <= loadids:
                raise ValueError('unknown FLEX baseline load')
        if record.get('kind') == 'BESS':
            if not 0 <= record['soc_min'] <= record['soc_initial'] <= record['soc_max'] <= 1:
                raise ValueError('illegal SOC bounds')
            if record['e_nameplate_mwh'] <= 0 or not 0 < record['eta_charge'] <= 1 or not 0 < record['eta_discharge'] <= 1:
                raise ValueError('illegal storage energy/efficiency')
        for low, high in [('p_min_mw', 'p_max_mw'), ('q_min_mvar', 'q_max_mvar')]:
            if low in record and high in record and record[low] > record[high]:
                raise ValueError('reversed resource bounds')
    children = []
    for interface in case['interfaces']:
        parent, child = interface['parent_network'], interface['child_network']
        if (parent, interface['parent_bus']) not in bus_keys or (child, interface['child_bus']) not in bus_keys:
            raise ValueError('unknown interface endpoint')
        if networks[parent]['layer'] != 'TN' or networks[child]['layer'] != 'DN':
            raise ValueError('unsupported interface direction/layers')
        if interface['child_bus'] != networks[child]['root_bus']:
            raise ValueError('interface must feed DN root')
        children.append(child)
    if set(children) != {n['id'] for n in case['networks'] if n['layer'] == 'DN'} or len(children) != len(set(children)):
        raise ValueError('each DN requires exactly one source interface')
    for mg in case.get('microgrids', []):
        if (mg['parent_dn'], mg['pcc_bus']) not in bus_keys:
            raise ValueError('unknown MG PCC')
    return {'valid': True, 'network_count': len(netids), 'bus_count': len(bus_keys),
            'device_count': len(case['devices']), 'load_count': len(loadids),
            'interval_count': ntime, 'interface_count': len(children),
            'microgrid_count': len(mgids), 'physical_validation': 'NOT_EVALUATED'}
