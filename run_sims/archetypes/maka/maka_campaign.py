import os
from datetime import datetime

import numpy as np
import pandas as pd
from emodpy_malaria.interventions.adherentdrug import adherent_drug
from emodpy_malaria.interventions.diag_survey import add_diagnostic_survey
from emodpy_malaria.interventions.drug_campaign import add_drug_campaign, drug_configs_from_code
from emodpy_malaria.interventions.irs import add_scheduled_irs_housing_modification
from emodpy_malaria.interventions.treatment_seeking import add_treatment_seeking
from emodpy_malaria.interventions.usage_dependent_bednet import add_scheduled_usage_dependent_bednet, \
    add_triggered_usage_dependent_bednet

from run_sims import manifest


# ======================================================================================
# SMC
# ======================================================================================

def smc_adherent_configuration(campaign, adherence=0.95, sp_resist_day1_multiply=0.87):
    # Copied from HBHI setup
    doses = [["Sulfadoxine", "Pyrimethamine",'Amodiaquine'],
             ['Amodiaquine'],
             ['Amodiaquine']]
    adherence_values = [sp_resist_day1_multiply, adherence, adherence]

    smc_adherent_config = adherent_drug(campaign=campaign,
                                        doses=doses,
                                        dose_interval=1,
                                        non_adherence_options=['Stop'],
                                        non_adherence_distribution=[1],
                                        adherence_values=adherence_values
                                        )
    return smc_adherent_config


def add_smc_by_coverage_and_start_day(campaign, coverage, start_days, agemin_years, agemax_years):
    # Copied from HBHI setup
    smc_adherent_drug_config = smc_adherent_configuration(campaign=campaign)

    add_drug_campaign(campaign=campaign,
                      campaign_type='SMC',
                      start_days=start_days,
                      coverage=coverage,
                      target_group={'agemin': agemin_years, 'agemax': agemax_years},
                      adherent_drug_configs=[smc_adherent_drug_config],
                      receiving_drugs_event_name='Received_SMC'
                      )


def add_smc(campaign, sim_start_year, smc_coverage_factor=1.0):
    # 2014: dates unknown, use 2016 days
    # 2015: dates unknown, use 2016 days
    # 2016: August 31, September 29, October 29
    # 2017: August 28, Sept 26, Oct 24
    # 2018: SMC performed, but no data
    # 2019: July 28th-August 1st, Aug 30-Sept 2nd, Sept 27-30th
    # 2020: July 24th, Aug 31-Sept 3, Sept ?
    # 2021: July 30-Aug 2nd, August 27-30, October 1-4

    df = pd.read_csv(os.path.join(manifest.maka_archetype_folder, "smc_maka.csv"))
    sim_start_date = f"{sim_start_year}-01-01"
    df["sim_day"] = df.apply(lambda x: convert_to_day(x["date"], sim_start_date), axis=1)

    # Group campaign events as much as possible.  Up to 2019, 3-11m had lower coverage.  2020 onwards, same coverage
    df1 = df[df["year"]<=2019]
    start_days = list(df1["sim_day"])
    add_smc_by_coverage_and_start_day(campaign, coverage=0.67 * smc_coverage_factor, start_days=start_days, agemin_years=0.33, agemax_years=1)
    add_smc_by_coverage_and_start_day(campaign, coverage=0.95 * smc_coverage_factor, start_days=start_days, agemin_years=1, agemax_years=10)

    df2 = df[df["year"] > 2019]
    start_days = list(df2["sim_day"])
    add_smc_by_coverage_and_start_day(campaign, coverage=0.95 * smc_coverage_factor, start_days=start_days, agemin_years=0.33, agemax_years=10)


def convert_to_day(convert_date, ref_date, date_format="%Y-%m-%d"):
    # Converts date to day of simulation starting from reference date
    # Uses actual calendar dates
    date_delta = datetime.strptime(convert_date, date_format) - \
                 datetime.strptime(ref_date, date_format)

    return date_delta.days

# ======================================================================================
# VC
# ======================================================================================

def add_irs(campaign, sim_start_year, irs_coverage_factor=1.):
    sim_start_date = f"{sim_start_year}-01-01"

    # 2020 - Fludora Fusion
    sim_day = convert_to_day("2020-06-15", sim_start_date)
    add_scheduled_irs_housing_modification(campaign,
                                           start_day=sim_day,
                                           demographic_coverage=0.95 * irs_coverage_factor,
                                           killing_initial_effect=0.8,
                                           killing_box_duration=195,
                                           killing_decay_time_constant=210,
                                           intervention_name="2020_Fludora_Fusion")

    # 2021 - SumiShield
    sim_day = convert_to_day("2021-06-15", sim_start_date)
    add_scheduled_irs_housing_modification(campaign,
                                           start_day=sim_day,
                                           demographic_coverage=0.95 * irs_coverage_factor,
                                           killing_initial_effect=0.95,
                                           killing_box_duration=195,
                                           killing_decay_time_constant=240,
                                           intervention_name="2021_SumiShield")




def add_itn(campaign, sim_start_year):
    # max usage: ~85% usage seen in peak of rainy season among people with access to nets. Koenker 2019

    default_itn_discard_rates = {
        "Expiration_Period_Distribution": "EXPONENTIAL_DISTRIBUTION",
        "Expiration_Period_Exponential": 465
    }
    # Trying to get ~50% discarded in 1.3 years (from ABV)

    slower_itn_discard_rates = {
        "Expiration_Period_Distribution": "EXPONENTIAL_DISTRIBUTION",
        "Expiration_Period_Exponential": 465*2.3
    }

    month_times = [
        0.0,
        30.417,
        60.833,
        91.25,
        121.667,
        152.083,
        182.5,
        212.917,
        243.333,
        273.75,
        304.167,
        334.583
    ]

    seasonal_itn_use = [0.3875, 0.755, 0.93, 1., 1., 1., 0.93, 0.755,0.5275, 0.5275, 0.3, 0.3]
    seasonal_use_config = {"Times": month_times, "Values": seasonal_itn_use}

    # 2016, 2019 campaigns.  Assume birthnet distributions ramps up in 2019
    sim_start_date = f"{sim_start_year}-01-01"
    add_bednets_for_population_and_births(campaign,
                                          start_day=convert_to_day("2016-06-01", sim_start_date),
                                          coverage=0.85,
                                          killing_initial_effect=0.6,
                                          discard_config=default_itn_discard_rates,
                                          seasonal_dependence=seasonal_use_config,
                                          include_birthnets=False
                                          )

    add_bednets_for_population_and_births(campaign,
                                          start_day=convert_to_day("2019-06-01", sim_start_date),
                                          coverage=0.85,
                                          killing_initial_effect=0.5,
                                          discard_config=default_itn_discard_rates,
                                          seasonal_dependence=seasonal_use_config,
                                          include_birthnets=False
                                          )

    # Add some bednets in to match early DHS timepoints on usage, but very uncertain on coverage
    start_day = convert_to_day("2010-06-01", sim_start_date)
    if start_day > 0:
        add_bednets_for_population_and_births(campaign,
                                              start_day=start_day,
                                              coverage=0.8,
                                              killing_initial_effect=0.65,
                                              discard_config=slower_itn_discard_rates,
                                              seasonal_dependence=seasonal_use_config,
                                              include_birthnets=False
                                              )

    # start_day = convert_to_day("2012-06-01", sim_start_date)
    # if start_day > 0:
    #     add_bednets_for_population_and_births(campaign,
    #                                           start_day=start_day,
    #                                           coverage=0.7,
    #                                           killing_initial_effect=0.7,
    #                                           discard_config=default_itn_discard_rates,
    #                                           seasonal_dependence=seasonal_use_config,
    #                                           include_birthnets=False
    #                                           )

    # 2014 net distribution (Julie Thwing).  This is also roughly when ANC net distributions started
    start_day = convert_to_day("2014-06-01", sim_start_date)
    if start_day > 0:
        add_bednets_for_population_and_births(campaign,
                                              start_day=start_day,
                                              coverage=0.95,
                                              killing_initial_effect=0.65,
                                              discard_config=slower_itn_discard_rates, #because 2014 was drought?
                                              seasonal_dependence=seasonal_use_config,
                                              include_birthnets=True
                                              )

    # Add even earlier bednets
    start_day = convert_to_day("2008-06-01", sim_start_date)
    if start_day > 0:
        add_bednets_for_population_and_births(campaign,
                                              start_day=start_day,
                                              coverage=0.25,
                                              killing_initial_effect=0.6,
                                              discard_config=default_itn_discard_rates,
                                              seasonal_dependence=seasonal_use_config,
                                              include_birthnets=False
                                              )

default_bednet_age_usage = {'youth_cov': 0.65,
                            'youth_min_age': 5,
                            'youth_max_age': 20}

default_itn_discard_config = {
    "Expiration_Period_Distribution": "DUAL_EXPONENTIAL_DISTRIBUTION",
    "Expiration_Period_Mean_1": 260,
    "Expiration_Period_Mean_2": 2106,
    "Expiration_Period_Proportion_1": 0.6
}
def add_bednets_for_population_and_births(campaign,
                                          coverage,
                                          start_day=1,
                                          seasonal_dependence=None,
                                          discard_config=None,
                                          age_dependence=default_bednet_age_usage,
                                          include_birthnets=True,
                                          birthnet_listening_duration=-1,
                                          killing_initial_effect=0.6,
                                          killing_box_duration=0,
                                          killing_decay_time_constant=1460.,
                                          blocking_initial_effect=0.9,
                                          blocking_box_duration=0,
                                          blocking_decay_time_constant=730.):

    if seasonal_dependence is None:
        seasonal_dependence = {}

    regular_bednets_event = add_scheduled_usage_dependent_bednet(campaign=campaign,
                                                                 start_day=start_day,
                                                                 demographic_coverage=coverage,
                                                                 age_dependence=age_dependence,
                                                                 seasonal_dependence=seasonal_dependence,
                                                                 discard_config=discard_config,
                                                                 killing_initial_effect=killing_initial_effect, #explicitly putting in killing/blocking even though these are defaults, in case UDBednet defaults change down the road
                                                                 killing_box_duration=killing_box_duration,
                                                                 killing_decay_time_constant=killing_decay_time_constant,
                                                                 blocking_initial_effect=blocking_initial_effect,
                                                                 blocking_box_duration=blocking_box_duration,
                                                                 blocking_decay_time_constant=blocking_decay_time_constant)

    if include_birthnets:
        birth_bednets_event = add_triggered_usage_dependent_bednet(campaign=campaign,
                                                                   trigger_condition_list=["Births"],
                                                                   start_day=start_day,
                                                                   demographic_coverage=coverage,
                                                                   age_dependence=age_dependence,
                                                                   seasonal_dependence=seasonal_dependence,
                                                                   discard_config=discard_config,
                                                                   listening_duration=birthnet_listening_duration,
                                                                   killing_initial_effect=killing_initial_effect,
                                                                   # explicitly putting in killing/blocking even though these are defaults, in case UDBednet defaults change down the road
                                                                   killing_box_duration=killing_box_duration,
                                                                   killing_decay_time_constant=killing_decay_time_constant,
                                                                   blocking_initial_effect=blocking_initial_effect,
                                                                   blocking_box_duration=blocking_box_duration,
                                                                   blocking_decay_time_constant=blocking_decay_time_constant)

def add_healthseeking(campaign, sim_start_year, hs_rate_factor=1.0):
    # For now, just assume 50% u5 health-seeking starting in 2010 (abrupt, but by the time we are looking at the data it shouldn't matter)
    start_day = np.max([1,convert_to_day("2010-01-01", f"{sim_start_year}-01-01")])

    u5_hs_rate = 0.5*hs_rate_factor #from DHS
    o5_hs_rate = 0.25*hs_rate_factor #made up
    u5_severe_hs_rate = 0.9
    o5_severe_hs_rate = 0.8

    target_list = [{'trigger': 'NewClinicalCase',
                    'coverage': u5_hs_rate,
                    'agemin': 0,
                    'agemax': 5,
                    'rate': 0.3},
                   {'trigger': 'NewClinicalCase',
                    'coverage': o5_hs_rate,
                    'agemin': 5,
                    'agemax': 100,
                    'rate': 0.3},
                   {'trigger': 'NewSevereCase',
                    'coverage': u5_severe_hs_rate,
                    'agemin': 0,
                    'agemax': 5,
                    'rate': 0.5},
                   {'trigger': 'NewSevereCase',
                    'coverage': o5_severe_hs_rate,
                    'agemin': 5,
                    'agemax': 100,
                    'rate': 0.5}]

    add_treatment_seeking(campaign=campaign,
                          start_day=start_day,
                          duration=-1,
                          targets=target_list,
                          drug=['Artemether', 'Lumefantrine'],
                          broadcast_event_name="Received_Treatment")



def add_pecadom_active_sweeps(campaign, sim_start_year, pecadom_coverage_factor=1.0, nmf_coverage_factor=1.0, include_pecadom_scaleup=True):
    import emod_api.interventions.common

    fever_detected_broadcast = emod_api.interventions.common.BroadcastEvent(campaign, Event_Trigger="Has_Fever")
    no_fever_detected_broadcast = emod_api.interventions.common.BroadcastEvent(campaign, Event_Trigger="Does_Not_Have_Fever")
    receiving_drugs_broadcast = emod_api.interventions.common.BroadcastEvent(campaign, Event_Trigger="Received_PECADOM_drugs")
    deliver_drug = drug_configs_from_code(campaign, drug_code="AL")

    receiving_drugs_with_malarial_fever = emod_api.interventions.common.BroadcastEvent(campaign, Event_Trigger="Received_PECADOM_drugs_with_malarial_fever")
    receiving_drugs_without_malarial_fever = emod_api.interventions.common.BroadcastEvent(campaign, Event_Trigger="Received_PECADOM_drugs_without_malarial_fever")

    sim_start_date = f"{sim_start_year}-01-01"

    if include_pecadom_scaleup:
        coverage_by_year = {2017: 0.45 * pecadom_coverage_factor,
                            2019: 0.5 * pecadom_coverage_factor,
                            2020: 0.55 * pecadom_coverage_factor,
                            2021: 0.6 * pecadom_coverage_factor,
                            2022: 0.65 * pecadom_coverage_factor}
    else:
        constant_coverage = 0.65 * pecadom_coverage_factor
        coverage_by_year = {2017: constant_coverage,
                            2019: constant_coverage,
                            2020: constant_coverage,
                            2021: constant_coverage,
                            2022: constant_coverage}

    # Weekly fever sweeps during transmission season
    # for y in range(2016,2022+1):
    for y in [2017,2019,2020,2021,2022]: #skip 2018 because of strike.
        add_diagnostic_survey(campaign,
                              coverage=coverage_by_year[y],
                              start_day=convert_to_day(f"{y}-08-01", sim_start_date),
                              repetitions=5*4,
                              tsteps_btwn_repetitions=7,
                              diagnostic_type="FEVER",
                              diagnostic_threshold=2, # Detection_Threshold of 2 would result in a positive diagnosis for temperatures above 39 degrees
                              event_name="PECADOM_active_sweep",
                              positive_diagnosis_configs=[fever_detected_broadcast],
                              negative_diagnosis_configs=[no_fever_detected_broadcast],
                              received_test_event="Screened_For_Fever"
                              )



    # Campaign events listening to test-and-treat based on the result of the fever screens
    add_diagnostic_survey(campaign,
                          coverage=1,
                          start_day=1,
                          diagnostic_type="PF_HRP2",
                          diagnostic_threshold=5,
                          trigger_condition_list=["Has_Fever"],
                          positive_diagnosis_configs=[receiving_drugs_broadcast, receiving_drugs_with_malarial_fever] + deliver_drug,
                          received_test_event="Screened_by_RDT"
                          )

    # Account for the fact that some non-malarial fevers will be found and then tested-and-treated
    add_diagnostic_survey(campaign,
                          coverage=0.1*nmf_coverage_factor, #approximate all-cause proportion of fevers, of which malaria-caused fevers are only a small fraction.  This number is, unfortunately, pretty uncertain
                          start_day=1,
                          diagnostic_type="PF_HRP2",
                          diagnostic_threshold=5,
                          trigger_condition_list=["Does_Not_Have_Fever"],
                          positive_diagnosis_configs=[receiving_drugs_broadcast, receiving_drugs_without_malarial_fever] + deliver_drug,
                          received_test_event="Screened_by_RDT"
                          )




def add_custom_events(campaign):
    # Add to custom events (used to do this by directly editing config.parameters.Custom_Individual_Events
    campaign.get_send_trigger("Received_Treatment", old=True)
    campaign.get_send_trigger("Received_Test", old=True)
    campaign.get_send_trigger("Received_Campaign_Drugs", old=True)
    campaign.get_send_trigger("Received_SMC", old=True)
    campaign.get_send_trigger("Bednet_Got_New_One", old=True)
    campaign.get_send_trigger("Bednet_Using", old=True)
    campaign.get_send_trigger("Bednet_Discarded", old=True)
    campaign.get_send_trigger("InfectionDropped", old=True)


def build_full_maka_campaign():
    import emod_api.campaign as campaign
    campaign.set_schema(manifest.schema_file)

    sim_start_year = 1962 # assumes 60 year simulation duration

    irs_coverage_factor = 0.8
    pecadom_coverage_factor = 1.0
    nmf_coverage_factor = 1.0
    smc_coverage_factor = 0.7
    hs_rate_factor = 0.8

    add_smc(campaign, sim_start_year=sim_start_year, smc_coverage_factor=smc_coverage_factor)
    add_irs(campaign, sim_start_year=sim_start_year, irs_coverage_factor=irs_coverage_factor)
    add_itn(campaign, sim_start_year=sim_start_year)
    add_healthseeking(campaign, sim_start_year=sim_start_year, hs_rate_factor=hs_rate_factor)
    add_pecadom_active_sweeps(campaign, sim_start_year=sim_start_year, pecadom_coverage_factor=pecadom_coverage_factor, nmf_coverage_factor=nmf_coverage_factor)

    add_custom_events(campaign)

    return campaign