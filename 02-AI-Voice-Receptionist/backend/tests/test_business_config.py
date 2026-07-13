import business_config


def test_business_configuration_is_complete() -> None:
    assert business_config.BUSINESS_NAME
    assert business_config.BUSINESS_LOCATION
    assert business_config.BUSINESS_HOURS
    assert business_config.BUSINESS_CONTACT["phone"]
    assert business_config.BUSINESS_CONTACT["email"]
    assert business_config.BUSINESS_SERVICES
    assert business_config.WELCOME_MESSAGE


def test_system_prompt_is_built_from_configuration() -> None:
    prompt = business_config.build_system_prompt()

    assert business_config.BUSINESS_NAME in prompt
    assert business_config.BUSINESS_LOCATION in prompt
    assert business_config.BUSINESS_SERVICES[0] in prompt
    assert business_config.BUSINESS_CONTACT["email"] in prompt
    for hours in business_config.BUSINESS_HOURS.values():
        assert hours in prompt


def test_appointment_configuration_has_a_prompt_for_every_field() -> None:
    assert set(business_config.APPOINTMENT_FIELDS) == set(
        business_config.APPOINTMENT_PROMPTS
    )

