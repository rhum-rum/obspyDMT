#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------
#   Filename:  test_fdsn_handler.py
#   Purpose:   testing fdsn_handler
#   Author:    Kasra Hosseini
#   Email:     hosseini@geophysik.uni-muenchen.de
#   License:   GPLv3
# -------------------------------------------------------------------

# -----------------------------------------------------------------------
# ----------------Import required Modules (Python and Obspy)-------------
# -----------------------------------------------------------------------

# Required Python and Obspy modules will be imported in this part.
import os
from obspy.core import UTCDateTime, read
from obspy.signal import seisSim

from obspyDMT.utils.event_handler import get_Events
from obspyDMT.utils.fdsn_handler import FDSN_network
from obspyDMT.utils.input_handler import command_parse, read_input_command
from obspyDMT.utils.instrument_handler import FDSN_ARC_IC


def test_FDSN_network():
    (options, args, parser) = command_parse()
    input_dics = read_input_command(parser)

    input_dics['min_date'] = '2011-03-01'
    input_dics['max_date'] = '2011-03-20'
    input_dics['min_mag'] = 8.9
    dir_name = int(UTCDateTime.now().timestamp)
    input_dics['datapath'] = 'test_%s' % dir_name
    input_dics['net'] = 'TA'
    input_dics['sta'] = 'Z3*'
    input_dics['cha'] = 'BHZ'
    input_dics['req_parallel'] = 'Y'
    input_dics['req_np'] = 4

    events = get_Events(input_dics, 'event-based')
    assert len(events) == 1

    FDSN_network(input_dics, events)

    st_raw = read(os.path.join(input_dics['datapath'],
                               '2011-03-01_2011-03-20_8.9_9.9',
                               '20110311_1',
                               'BH_RAW', '*'))
    assert len(st_raw) == 7

    st_wilber = read(os.path.join('tests', 'fdsn_waveforms', 'TA*'))

    for sta in ['Z35A', 'Z37A', 'Z39A']:
        tr_raw = st_raw.select(station=sta)[0]
        tr_wilber = st_wilber.select(station=sta)[0]
        tr_diff = abs(tr_raw.data - tr_wilber.data)
        assert max(tr_diff) == 0.

    FDSN_ARC_IC(input_dics, input_dics['fdsn_base_url'])

    st_cor = read(os.path.join(input_dics['datapath'],
                               '2011-03-01_2011-03-20_8.9_9.9',
                               '20110311_1',
                               'BH', '*'))
    assert len(st_cor) == 7

    paz_35 = {'gain': 5.714000e+08,
              'sensitivity': 6.309070e+08,
              'zeros': (0.0, 0.0, 0.0),
              'poles': (-3.701000e-02+3.701000e-02j,
                        -3.701000e-02-3.701000e-02j,
                        -1.131000e+03+0.000000e+00j,
                        -1.005000e+03+0.000000e+00j,
                        -5.027000e+02+0.000000e+00j)}

    for sta in ['Z35A', 'Z37A', 'Z39A']:
        tr_cor = st_cor.select(station=sta)[0]
        tr_wilber = st_wilber.select(station=sta)[0]
        tr_wilber_corr = tr_wilber.copy()
        corr_wilber = seisSim(tr_wilber.data,
                              tr_wilber.stats.sampling_rate,
                              paz_remove=paz_35,
                              paz_simulate=None,
                              remove_sensitivity=True,
                              simulate_sensitivity=False,
                              water_level=600.,
                              zero_mean=True,
                              taper=True,
                              taper_fraction=0.05,
                              pre_filt=(0.008, 0.012, 3.0, 4.0),
                              pitsasim=False,
                              sacsim=True)
        tr_wilber_corr.data = corr_wilber
        tr_diff = abs(tr_cor.data - tr_wilber_corr.data)
        # amplitude of the traces is in the order of 1e6 or so
        assert max(tr_diff) < 0.001


