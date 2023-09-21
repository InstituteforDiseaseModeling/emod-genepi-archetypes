import os

import pandas as pd
from emodpy_malaria.interventions.treatment_seeking import add_treatment_seeking

from run_sims import manifest
from run_sims.helpers import convert_to_day_365


def add_hs_by_age_and_severity(campaign,
                               u5_hs_rate,
                               o5_hs_rate=None,
                               u5_severe_hs_rate=0.9,
                               o5_severe_hs_rate=0.8,
                               node_ids=None,
                               start_day=1,
                               duration=-1,
                               drug=['Artemether', 'Lumefantrine']):
    if o5_hs_rate is None:
        o5_hs_rate = u5_hs_rate * 0.5

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
                          node_ids=node_ids,
                          start_day=start_day,
                          duration=duration,
                          targets=target_list,
                          drug=drug,
                          broadcast_event_name="Received_Treatment")


def add_hs(campaign, sim_start_date):
    df = pd.read_csv(os.path.join(manifest.magude_archetype_folder, "hs_magude.csv"))

    # Add simday column for adding to campaign file
    df['simday'] = [convert_to_day_365(x, sim_start_date, "%Y-%m-%d") for x in df.fulldate]

    for i, row in df.iterrows():
        add_hs_by_age_and_severity(campaign,
                                   start_day=row["simday"],
                                   u5_hs_rate=row["cov_newclin_youth"],
                                   o5_hs_rate=row["cov_newclin_adult"],
                                   u5_severe_hs_rate=row["cov_severe_youth"],
                                   o5_severe_hs_rate=row["cov_severe_adult"],
                                   duration=row["duration"])
