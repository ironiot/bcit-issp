from elm.obd_message import ECU_ADDR_E, ECU_R_ADDR_E, HD, SZ, DT

ObdMessage = {
    'car': {
        'STATUS': {
            'Request': '^0101[0-9A-F]*$',
            'Descr': 'Status since DTCs cleared',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('41 01 81 07 A1 00'),
        },
        'SHOW_DIAG_TC': {
            'Request': '^03[0-9A-F]*$',
            'Descr': 'Show stored DTCs',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('43 01 04 20'),
        },
        'SHOW_PENDING_TC': {
            'Request': '^07[0-9A-F]*$',
            'Descr': 'Show pending DTCs',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('47 01 04 20'),
        },
        'DTC_DTCFRZF': {
            'Request': '^0102[0-9A-F]*$',
            'Descr': 'DTC that triggered freeze frame',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('41 02 04 20'),
        },
        'DTC_ENGINE_LOAD': {
            'Request': '^0204[0-9A-F]*$',
            'Descr': 'Freeze: engine load',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('42 04 00 80'),
        },
        'DTC_COOLANT_TEMP': {
            'Request': '^0205[0-9A-F]*$',
            'Descr': 'Freeze: coolant temp',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('42 05 00 82'),
        },
        'DTC_RPM': {
            'Request': '^020C[0-9A-F]*$',
            'Descr': 'Freeze: RPM',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('05') + DT('42 0C 00 1F 40'),
        },
        'DTC_SPEED': {
            'Request': '^020D[0-9A-F]*$',
            'Descr': 'Freeze: vehicle speed',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('42 0D 00 3C'),
        },
    },
    'two_dtcs': {
        'STATUS': {
            'Request': '^0101[0-9A-F]*$',
            'Descr': 'Status (MIL on, 2 DTCs)',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('41 01 82 07 A1 00'),
        },
        'SHOW_DIAG_TC': {
            'Request': '^03[0-9A-F]*$',
            'Descr': 'Show stored DTCs (P0420, P0301)',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('43 02 04 20 03 01'),
        },
        'SHOW_PENDING_TC': {
            'Request': '^07[0-9A-F]*$',
            'Descr': 'Show pending DTCs',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('47 02 04 20 03 01'),
        },
        'DTC_DTCFRZF': {
            'Request': '^0102[0-9A-F]*$',
            'Descr': 'DTC that triggered freeze frame',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('41 02 04 20'),
        },
        'DTC_ENGINE_LOAD': {
            'Request': '^0204[0-9A-F]*$',
            'Descr': 'Freeze: engine load',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('42 04 00 80'),
        },
        'DTC_COOLANT_TEMP': {
            'Request': '^0205[0-9A-F]*$',
            'Descr': 'Freeze: coolant temp',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('42 05 00 82'),
        },
        'DTC_RPM': {
            'Request': '^020C[0-9A-F]*$',
            'Descr': 'Freeze: RPM',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('05') + DT('42 0C 00 1F 40'),
        },
        'DTC_SPEED': {
            'Request': '^020D[0-9A-F]*$',
            'Descr': 'Freeze: vehicle speed',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('42 0D 00 3C'),
        },
    },
}
