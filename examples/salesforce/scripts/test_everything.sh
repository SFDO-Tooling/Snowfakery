cci org scratch_delete snowfakery_test_temp
cci org scratch dev snowfakery_test_temp --days 1
cci flow run test_everything --org snowfakery_test_temp
