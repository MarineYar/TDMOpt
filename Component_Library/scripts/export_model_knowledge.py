"""Export component descriptions from this public library; no RAG or LLM."""
import ast
import json
from pathlib import Path
from tdm_workflow_agent.model_component.registry import REGISTRY, TN_BASE_MODELS, DN_BASE_MODELS
import tdm_workflow_agent.model_component as package

ROOT = Path(__file__).resolve().parents[1]
MC = Path(package.__file__).parent


def network_notes(filename):
    tree = ast.parse((MC / filename).read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Subscript):
            if any(isinstance(t, ast.Attribute) and t.attr == '_formulation_notes' for t in node.targets):
                return ast.literal_eval(node.value.value)
    raise ValueError(filename)


notes = {**network_notes('case_tn_models.py'), **network_notes('case_dn_models.py')}
# These are implementation clarifications, not claims from private experiments.
notes.update({
    'MG_GT_UC': 'MG GT commitment, startup and shutdown are continuous [0,1]; two-hour minimum-up inequalities are retained without integer guarantees.',
    'MG_BESS_PRECONDITION': 'Require MG energy at the configured target boundary (default 16 h) >= .8 * soc_max * e_nameplate. A short horizon or absent MG BESS gives an empty/not_applicable constraint list.',
    'MG_FLEX_PEAK_SHAVING': 'Cap each child-DN net interface import at .9 of its non-MG peak load. May be infeasible; no automatic load shedding or fallback.',
    'OBJ_GT_RAMPING': 'Squared consecutive active TN GEN output changes, not MG GT ramping; default weight 10 and dt scaling.',
    'OBJ_INTERFACE_USAGE': 'Squared receiving-end interface P, default weight 1 with additional fixed .1 normalization and dt scaling.',
    'OBJ_LOSS_PENALTY': 'Default weight 5 on internal network ell summed over branches/time with dt; not a literal r*ell physical MW loss and excludes interface ell.',
    'OBJ_VOLTAGE_DEVIATION': 'Squared departure of available v (TN linearized) or u=V^2 from 1. TN factor .1. The source implementation checks for u before including a network; preserve its existing behavior.',
    'CON_LOAD_SHEDDING_LIMIT': 'No controllable load-shedding variable: load shedding is fixed at zero by construction.',
    'OBJ_LOAD_SHEDDING': 'No load-shedding objective variable in this canonical path; reported shedding is zero.',
    'MG_BESS_SOC_MODEL': 'Energy in MWh on N+1 boundaries with per-device efficiencies, dt and initial/terminal energy. Storage mode is continuous [0,1], not exact binary charge/discharge exclusion.',
    'CON_DN_BESS_CH_DIS_MUTEX': 'Continuous [0,1] storage mode envelope; simultaneous partial charge/discharge is not strictly excluded.',
    'CON_MG_BESS_CH_DIS_MUTEX': 'Continuous [0,1] storage mode envelope; simultaneous partial charge/discharge is not strictly excluded.',
})
variable_groups = {
    'TN': ['network[tn].pf', 'network[tn].pt', 'network[tn].qf/qt (AC only)', 'network[tn].e/f/u or v/theta or wr/wi (formulation-dependent)'],
    'DN': ['network[dn].pf/qf/pt/qt', 'network[dn].u', 'network[dn].ell (current-based variants)'],
    'MG': ['pg[device,t]', 'charge/discharge[bess,t]', 'energy[bess,k]', 'mg_p/mg_q[mg,t]'],
    'Objective': ['existing network/resource/interface states; objective components share obj'],
    'Constraint': ['existing network/resource/interface states; constraints can be integrated or variable bounds'],
    'Coordination': ['port_p/port_q[port,t]', 'tap[port,t]'],
}
cards=[]
for comp in sorted(REGISTRY.list_components(selectable_only=False),key=lambda c:c.component_id):
    card=comp.to_dict()
    card['description_cn']=comp.description_cn
    card['description_en']=notes.get(comp.component_id,comp.description_en)
    card['formal_selectable']=comp.selection_mode in {'adaptive_exclusive','adaptive_multi_select'}
    card['component_layer']=comp.layer
    card['variables']=variable_groups[comp.layer]
    card['variables_note']='Shared model states; indexed by network, device and time as applicable.'
    card['assumptions']=['balanced steady-state networks', 'radial series-only DN; TN may be meshed', 'explicit device data and finite full-horizon profiles']
    card['topology_applicability']={'TN':'balanced; meshed allowed','DN':'balanced radial; no internal charging/taps/phase shift','MG':'aggregate injection; no internal topology'}
    card['requires']=(['parent model.T, destination block, explicit network records, injection(bus,time,quantity) callback'] if comp.component_id in TN_BASE_MODELS | DN_BASE_MODELS else ['validated tdm_case_v1 case and matching scenario', 'one TN base and one supported DN base'])
    card['provides']=[comp.component_id]
    card['solver_requirements']='Pyomo model construction; use a continuous nonlinear solver for the assembled NLP.'
    card['limitations']=([notes[comp.component_id]] if comp.component_id in notes else [])
    card['implementation_status']='included_canonical_assembly'
    card['call_signature']=('build_tn_network(model, block, network, component_id, injection)' if comp.component_id in TN_BASE_MODELS else 'build_dn_network(model, block, network, component_id, injection)' if comp.component_id in DN_BASE_MODELS else 'build_case_model(selected_ids, case, scenario, method_config)')
    cards.append(card)
payload={'schema_version':'public_component_cards_v1','scope':'TN, DN and aggregate MG model components', 'cards':cards}
(MC/'model_knowledge.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# 组件说明 / Component Cards','', '共 59 个注册条目：20 个可选项和 39 个随模型组装的核心条目。', '', 'TN 为平衡网络，DN 为平衡径向网络，MG 为聚合模型。输入、变量单位和通用假设见 [data_contract.md](data_contract.md)，调用方法见 [composition.md](composition.md)。', '']
for card in cards:
    lines.extend(['## '+card['component_id'],'', '- 层: '+card['layer']+'；组合角色: `'+card['selection_mode']+'`', '- 名称: '+card['name_cn'], '- 功能: '+card['description_en'], '- 入口: `'+card['builder_import_path']+'`', '- 签名: `'+card['call_signature']+'`', '- 状态变量引用: '+', '.join('`'+v+'`' for v in card['variables']), '- 依赖: '+'; '.join(card['requires']), ''])
(ROOT/'docs').mkdir(exist_ok=True)
(ROOT/'docs/components.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'Exported {len(cards)} cards')
