from policyengine_api.country import (
    COUNTRIES,
    validate_country,
    PolicyEngineCountry,
)
from policyengine_api.utils import get_safe_json
from policyengine_core.parameters import ParameterNode, Parameter, ParameterScale, ParameterScaleBracket


def metadata(country_id: str):
    """
    /<country_id>/metadata (GET)

    Returns metadata about the country's tax and benefit system needed by the PolicyEngine web app.
    """
    country = COUNTRIES.get(country_id)
    country_not_found = validate_country(country_id)
    if country_not_found:
        return country_not_found
    return dict(
        status="ok",
        message=None,
        result=dict(
            variables=build_variables(country),
            parameters=build_parameters(country),
            entities=build_entities(country),
            variableModules=country.tax_benefit_system.variable_module_metadata,
            economy_options=build_microsimulation_options(country, country_id),
            current_law_id=1 if country_id == "uk" else 2,
        ),
    )


def build_microsimulation_options(country: PolicyEngineCountry, country_id: str) -> dict:
    # { region: [{ name: "uk", label: "the UK" }], time_period: [{ name: 2022, label: "2022", ... }] }
    options = dict()
    if country_id == "uk":
        region = [
            dict(name="uk", label="the UK"),
            dict(name="ni", label="Northern Ireland"),
        ]
        time_period = [
            dict(name=2022, label="2022"),
        ]
        options["region"] = region
        options["time_period"] = time_period
    elif country_id == "us":
        region = [
            dict(name="us", label="the US"),
            dict(name="ak", label="Alaska"),
            dict(name="fl", label="Florida"),
            dict(name="md", label="Maryland"),
            dict(name="ma", label="Massachusetts"),
            dict(name="nv", label="Nevada"),
            dict(name="ny", label="New York"),
            dict(name="or", label="Oregon"),
            dict(name="pa", label="Pennsylvania"),
            dict(name="sd", label="South Dakota"),
            dict(name="tn", label="Tennessee"),
            dict(name="tx", label="Texas"),
            dict(name="wa", label="Washington"),
        ]
        time_period = [
            dict(name=2022, label="2022"),
        ]
        options["region"] = region
        options["time_period"] = time_period
    return options


def build_variables(country: PolicyEngineCountry) -> dict:
    variables = country.tax_benefit_system.variables
    variable_data = {}
    for variable_name, variable in variables.items():
        variable_data[variable_name] = {
            "documentation": variable.documentation,
            "entity": variable.entity.key,
            "valueType": variable.value_type.__name__,
            "definitionPeriod": variable.definition_period,
            "name": variable_name,
            "label": variable.label,
            "category": variable.category,
            "unit": variable.unit,
            "moduleName": variable.module_name,
            "indexInModule": variable.index_in_module,
            "isInputVariable": variable.is_input_variable(),
            "defaultValue": variable.default_value
            if isinstance(variable.default_value, (int, float, bool))
            else None,
            "adds": variable.adds,
            "subtracts": variable.subtracts,
        }
        if variable.value_type.__name__ == "Enum":
            variable_data[variable_name]["possibleValues"] = [
                dict(value=value.name, label=value.value) for value in variable.possible_values
            ]
            variable_data[variable_name]["defaultValue"] = variable.default_value.name
    return variable_data


def build_parameters(country: PolicyEngineCountry) -> dict:
    parameters = country.tax_benefit_system.parameters
    parameter_data = {}
    for parameter in parameters.get_descendants():
        if "gov" != parameter.name[:3]:
            continue
        if isinstance(parameter, ParameterScale) or isinstance(parameter, ParameterScaleBracket):
            continue
        if isinstance(parameter, Parameter):
            parameter_data[parameter.name] = {
                "type": "parameter",
                "parameter": parameter.name,
                "description": parameter.description,
                "label": parameter.metadata.get("label"),
                "unit": parameter.metadata.get("unit"),
                "period": parameter.metadata.get("period"),
                "values": {
                    value_at_instant.instant_str: get_safe_json(
                        value_at_instant.value
                    )
                    for value_at_instant in parameter.values_list
                },
            }
        elif isinstance(parameters, ParameterNode):
            parameter_data[parameter.name] = {
                "type": "parameterNode",
                "parameter": parameter.name,
                "description": parameter.description,
                "label": parameter.metadata.get("label"),
            }
    return parameter_data


def build_entities(country: PolicyEngineCountry) -> dict:
    data = {}
    for entity in country.tax_benefit_system.entities:
        entity_data = {
            "plural": entity.plural,
            "label": entity.label,
            "doc": entity.doc,
            "is_person": entity.is_person,
            "key": entity.key,
        }
        if hasattr(entity, "roles"):
            entity_data["roles"] = {
                role.key: {
                    "plural": role.plural,
                    "label": role.label,
                    "doc": role.doc,
                }
                for role in entity.roles
            }
        else:
            entity_data["roles"] = {}
        data[entity.key] = entity_data
    return data