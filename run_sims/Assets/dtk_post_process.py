import json
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


from datetime import datetime, timedelta
from dateutil import relativedelta

def get_archetype_name():
    with open("config.json", 'r') as f:
        d = json.load(f)
    return d["archetype"]

def summarize_endpoint():
    # Summarize endpoint
    event_recorder_filepath = os.path.join("output", "InsetChart.json")
    with open(event_recorder_filepath, 'r') as f:
        d = json.load(f)

    endpoint_data = {
        "rdt_prev": np.mean(np.array(d["Channels"]["PfHRP2 Prevalence"]["Data"])[-365:]),
        "true_prev": np.mean(np.array(d["Channels"]["True Prevalence"]["Data"])[-365:])
        # "average_biting"
    }

    json.dump(endpoint_data, open(os.path.join("output", "endpoint.json"), 'w'))

def make_archetype_plots():
    archetype = get_archetype_name()

    if archetype == "maka_historical":
        sim_start_year = 1962
        compare_to_dhs_maka(sim_start_year)
        compare_to_school_survey_maka(sim_start_year)

    elif archetype == "magude_historical":
        sim_start_year = 1959
        compare_prev_magude(sim_start_year)
        compare_incidence_magude(sim_start_year)

# ===============
# Maka_historical
# ===============
def convert_to_date_365(convert_day, ref_date, date_format="%Y-%m-%d"):
    # Converts day of simulation starting from reference date into date
    # Assumes a calendar year has exactly 365 days

    convert_year = int(int(convert_day) / 365) + datetime.strptime(ref_date, date_format).year
    convert_day = convert_day - int(int(convert_day) / 365) * 365
    return datetime.strftime(datetime(convert_year, 1, 1) + timedelta(convert_day - 1), date_format)


def compare_to_dhs_maka(sim_start_year):
    # Compare to DHS data
    binned_report_filepath = os.path.join("output", "BinnedReport.json")

    # Check if binned report exists
    if not os.path.isfile(binned_report_filepath):
        return

    with open(binned_report_filepath, "r") as f:
        data_binned = json.load(f)

    # Report channels are binned by age.  Bin 0 is under-5s
    n = data_binned['Channels']['Population']['Data'][0]
    n_pos = data_binned['Channels']['PfHRP2 Positive']['Data'][0]
    frac_pos = np.array(n_pos) / np.array(n)

    df_sim = pd.DataFrame({"sim_day": np.arange(len(frac_pos)), "pos_frac_sim": frac_pos})
    df_sim["date"] = df_sim["sim_day"].apply(lambda x: convert_to_date_365(x, f"{sim_start_year}-01-01"))

    df_dhs = pd.read_csv(os.path.join("Assets", "maka_dhs_prevalence_summary.csv"))
    yerr = np.array([df_dhs["pos_frac"] - df_dhs["pos_frac_low"],
                     df_dhs["pos_frac_high"] - df_dhs["pos_frac"]])

    # Plot comparison
    plt.figure(figsize=(10, 5), dpi=200)
    plt.plot_date(pd.to_datetime(df_sim["date"]), df_sim["pos_frac_sim"], ls='-', marker=None)
    plt.errorbar(pd.to_datetime(df_dhs["survey-date"]), df_dhs["pos_frac"], yerr=yerr, ls='none', marker='o')
    plt.ylabel("Under-5 RDT-positive fraction")

    plt.xlim([pd.to_datetime("2010-01-01"), pd.to_datetime("2023-01-01")])
    plt.savefig("u5_prev.png")

    # Save comparison data
    df_save = pd.merge(df_dhs, df_sim, how="left", left_on="survey-date", right_on="date")
    df_save.to_csv("u5_prev_data.csv", index=False)


def compare_to_school_survey_maka(sim_start_year):
    # Compare to school_survey data

    binned_report_filepath = os.path.join("output", "BinnedReport.json")

    # Check if binned report exists
    if not os.path.isfile(binned_report_filepath):
        return

    with open(binned_report_filepath, "r") as f:
        data_binned = json.load(f)

    # Report channels are binned by age.  Bin 1 is 5-9, Bin 2 is 10-14
    n = np.array(data_binned['Channels']['Population']['Data'][1]) + np.array(
        data_binned['Channels']['Population']['Data'][2])
    n_pos = np.array(data_binned['Channels']['PfHRP2 Positive']['Data'][1]) + np.array(
        data_binned['Channels']['PfHRP2 Positive']['Data'][2])
    frac_pos = np.array(n_pos) / np.array(n)

    df_sim = pd.DataFrame({"sim_day": np.arange(len(frac_pos)), "pos_frac_sim": frac_pos})
    df_sim["date"] = df_sim["sim_day"].apply(lambda x: convert_to_date_365(x, f"{sim_start_year}-01-01"))

    # Plot comparison
    plt.figure(figsize=(10, 5), dpi=200)
    plt.plot_date(pd.to_datetime(df_sim["date"]), df_sim["pos_frac_sim"], ls='-', marker=None)

    # School survey
    yerr = np.array([[0.031], [0.061]])
    plt.errorbar(x=[pd.to_datetime("2021-12-03")], y=[0.046], yerr=yerr, fmt='o', c="C1",
                 label="School survey (ages 6-15)")
    plt.ylabel("School-age RDT-positive fraction")
    # plt.xlim(["2010-01-01", "2023-01-01"])
    plt.xlim([pd.to_datetime("2010-01-01"), pd.to_datetime("2023-01-01")])
    plt.savefig("sac_prev.png")

    # Save comparison data
    df_save = pd.DataFrame({"date": "2021-12-03",
                            "pos_frac": 0.046,
                            "pos_frac_low": 0.031,
                            "pos_frac_high": 0.061,
                            "n_pos": 34,
                            "n": 739,
                            "pos_frac_sim": df_sim[df_sim["date"] == "2021-12-03"]["pos_frac_sim"].iloc[0]
                            },
                           index=[0]
                           )
    df_save.to_csv("sac_prev_data.csv", index=False)



# =================
# Magude_historical
# =================

def compare_prev_magude(sim_start_year):
    with open(os.path.join("output","InsetChart.json"), "r") as f:
        d = json.load(f)
    sim_df = pd.DataFrame({
        "t": np.arange(len(d['Channels']['PfHRP2 Prevalence']['Data'])),
        "prev": d['Channels']['PfHRP2 Prevalence']['Data']})
    sim_df["date"] = sim_df["t"].apply(lambda x: convert_to_date_365(x, f"{sim_start_year}-01-01"))

    prev_df = pd.read_csv(os.path.join("Assets", "magude_prevalence.csv"))
    prev_df['y_err_lower'] = prev_df['pos_frac'] - prev_df['pos_frac_low']
    prev_df['y_err_upper'] = prev_df['pos_frac_high'] - prev_df['pos_frac']

    plt.close('all')
    plt.figure(dpi=200)
    plt.plot_date(pd.to_datetime(sim_df["date"]), sim_df["prev"], ls='-', marker=None, label="sim")
    plt.xlim([pd.to_datetime("2010-01-01"), pd.to_datetime("2020-01-01")])
    plt.errorbar(x=pd.to_datetime(prev_df["survey-date"]), y=prev_df["pos_frac"], yerr=[prev_df['y_err_lower'], prev_df['y_err_upper']], fmt='o', c="C1", label="ref")
    plt.legend()
    plt.savefig("magude_prev.png")

def compare_incidence_magude(sim_start_year):
    with open(os.path.join("output","ReportEventCounter.json"), "r") as f:
        d = json.load(f)
    day_to_month = [1] * 31 + [2] * 28 + [3] * 31 + [4] * 30 + [5] * 31 + [6] * 30 \
                   + [7] * 31 + [8] * 31 + [9] * 30 + [10] * 31 + [11] * 30 + [12] * 31

    cases = np.array(d["Channels"]["Received_Treatment"]["Data"])

    sim_duration_years = np.round(len(cases) / 365).astype(int)
    year = np.repeat(np.arange(sim_duration_years), 365)
    month = []
    for i in range(sim_duration_years):
        month += day_to_month

    sim_data = pd.DataFrame({'year': year[:-1], # omit the last year and month value since Emod no longer reports it.
                             'month': month[:-1],
                             'cases': cases})
    # Aggregate by month:
    sim_data = sim_data.groupby(['year', 'month']).agg({"cases": "sum"}).reset_index()
    sim_data["year_actual"] = sim_data["year"] + sim_start_year
    sim_data['first_day_of_month'] = pd.to_datetime(
        sim_data['year_actual'].astype(str) + '-' + sim_data['month'].astype(str) + '-01')

    inc_data = pd.read_csv(os.path.join("Assets", "magude_incidence.csv"))

    # Need to rescale incidence depending on simulation size. True catchment has about 44k people
    with open("config.json", 'r') as f:
        config_dict = json.load(f)
    sim_pop_size = 1000*config_dict["population_size_in_thousands"]

    plt.close('all')
    plt.figure(dpi=200)
    plt.plot_date(sim_data["first_day_of_month"], sim_data["cases"], fmt='-')
    plt.plot_date(pd.to_datetime(inc_data["fulldate"]), inc_data["cases"] * (sim_pop_size / inc_data["pop"]), fmt=".-")
    plt.xlim([pd.to_datetime("2013-01-01"), pd.to_datetime("2019-01-01")])
    plt.savefig("magude_inc.png")

def application(output_folder="output"):
    print("starting dtk post process!")

    summarize_endpoint()

    make_archetype_plots()


if __name__ == "__main__":
    # Placeholder for now
    application(output_folder="output")
    # application(output_folder='.') #for testing