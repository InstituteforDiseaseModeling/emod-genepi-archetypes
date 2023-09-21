import argparse

from run_sims import manifest
from run_sims.create_sim_sweeps import create_and_run_sim_sweep


class NullableFloatListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if any(str(item).lower() == "none" for item in values): # values.lower() == "none":
            setattr(namespace, self.dest, None)
        else:
            float_list = [float(item) for item in values]
            setattr(namespace, self.dest, float_list)


def main():

    parser = argparse.ArgumentParser(description='Run simulations from command line')
    parser.add_argument('--exp_id_filepath', '-i', type=str,
                        help='emod experiment id file (default to manifest.exp_id_file)',
                        default=manifest.exp_id_file)
    parser.add_argument('--archetypes', '-a', nargs='+', type=str,
                        help='list of values for Archetypes: test, flat, maka_like, magude_like, maka_historical, '
                             'magude_historical (default to ["test"]).', default=['test'])
    parser.add_argument('--pop_sizes_in_thousands', '-p', nargs='+', type=int,
                        help='list of values for population size in thousands (possible values are 1k,10k,20k,50k,100k,'
                             ' default to [1, 10])',
                        default=[1, 10])
    parser.add_argument('--importations_per_year_per_1000', '-r', nargs='+', type=int,
                        help='list of values for importation rate per 1000 people in population (default to [50])',
                        default=[50])
    parser.add_argument('--target_prevalences', '-t', nargs='+', type=str,
                        help='list of values for target (RDT) prevalence for test/flat/maka_like/magude_like scenarios'
                             ' (possible values are 5%%, 10%%, 20%%, 30%%, 40%%, default to [0.05])',
                        default=[0.05], action=NullableFloatListAction)
    parser.add_argument('--max_individual_infections', '-m', nargs='+', type=int,
                        help='list of values for maximum number of concurrent infections to sweep '
                             '(default to [3])',
                        default=[3])
    # parser.add_argument('--larval_habitat_scales', '-l', nargs='+', type=float,
    #                     help='list of values for the log10 of the maximum larval habitat to sweep '
    #                          '(default to [6.5, 7.0, 7.5])',
    #                     default=[6.5, 7.0, 7.5])
    parser.add_argument('--seeds', '-s', type=int, help='number of simulation replicates (default to 3)',
                        default=3)
    # parser.add_argument('--reporting_interval', '-r', type=int,
    #                     help='reporting interval for ReportInfectionStatsMalaria (default to 30 days)', default=30)
    parser.add_argument('--exp_name', '-e', type=str,
                        help='emod experiment name in Comps (default to emod_genepi_archetypes)',
                        default='mpg e2e test')
    args = parser.parse_args()

    create_and_run_sim_sweep(archetypes=args.archetypes,
                             pop_sizes_in_thousands=args.pop_sizes_in_thousands,
                             importations_per_year_per_1000=args.importations_per_year_per_1000,
                             target_prevalences=args.target_prevalences,
                             max_num_infections=args.max_individual_infections,
                             number_of_seeds=args.seeds,
                             experiment_name=args.exp_name,
                             exp_id_filepath=args.exp_id_filepath)


if __name__ == "__main__":
    main()
