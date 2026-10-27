"""Explicit graph and ownership indices; no arithmetic bus/name inference."""
from __future__ import annotations


def network_index(network: dict) -> dict:
    buses = [b['id'] for b in network['buses']]
    if len(set(buses)) != len(buses):
        raise ValueError('duplicate bus ID')
    adjacency = {bus: [] for bus in buses}
    incident = {bus: [] for bus in buses}
    branch_ids = set()
    active = 0
    for branch in network['branches']:
        if branch['id'] in branch_ids:
            raise ValueError('duplicate branch ID')
        branch_ids.add(branch['id'])
        f, t = branch['from_bus'], branch['to_bus']
        if f not in adjacency or t not in adjacency:
            raise ValueError('unknown branch bus')
        if branch['status'] not in (0, 1):
            raise ValueError('invalid branch status')
        if not branch['status']:
            continue
        active += 1
        adjacency[f].append(t)
        adjacency[t].append(f)
        incident[f].append(branch['id'])
        incident[t].append(branch['id'])
    root = network.get('root_bus') if network['layer'] == 'DN' else network.get('reference_bus')
    if root not in adjacency:
        raise ValueError('missing root/reference bus')
    parent, children, order = {root: None}, {b: [] for b in buses}, [root]
    for bus in order:
        for child in adjacency[bus]:
            if child not in parent:
                parent[child] = bus
                children[bus].append(child)
                order.append(child)
    if len(order) != len(buses):
        raise ValueError(f"{network['id']}: disconnected/islanded network")
    if network['layer'] == 'DN' and active != len(buses) - 1:
        raise ValueError(f"{network['id']}: radial DN required; cycle/parallel branch present")
    result = {'bus_to_row': {b: i for i, b in enumerate(buses)}, 'incident_branches': incident,
              'active_branch_count': active, 'connected_components': [order]}
    if network['layer'] == 'DN':
        result.update(parent=parent, children=children, postorder=list(reversed(order)))
    return result


def build_indices(case: dict) -> dict:
    local_to_global, global_to_local, incident = {}, {}, {}
    networks = {}
    for network in case['networks']:
        networks[network['id']] = network_index(network)
        for bus in network['buses']:
            key = network['id'], bus['id']
            gid = len(local_to_global)
            local_to_global[key] = gid
            global_to_local[gid] = key
            incident[key] = networks[network['id']]['incident_branches'][bus['id']]
    return {'local_to_global': local_to_global, 'global_to_local': global_to_local,
            'resource_to_bus': {d['id']: (d['network_id'], d['bus_id']) for d in case['devices']},
            'interface_by_child': {i['child_network']: i for i in case['interfaces']},
            'incident_branches': incident, 'networks': networks}
