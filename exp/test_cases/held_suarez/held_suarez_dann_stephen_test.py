import numpy as np

from isca import DryCodeBase, DiagTable, Experiment, Namelist, GFDL_BASE

NCORES = 16
RESOLUTION = 'T42', 25  # T42 horizontal resolution, 25 levels in pressure ##DMM could change T213 but this is very high, T170 is more standard. If you change pressure levels, you need to think about where those extra levecls go (in spectral_dynamics)

# a CodeBase can be a directory on the computer,
# useful for iterative development
cb = DryCodeBase.from_directory(GFDL_BASE)

# or it can point to a specific git repo and commit id.
# This method should ensure future, independent, reproducibility of results.
# cb = DryCodeBase.from_repo(repo='https://github.com/isca/isca', commit='isca1.1')

# compilation depends on computer specific settings.  The $GFDL_ENV
# environment variable is used to determine which `$GFDL_BASE/src/extra/env` file
# is used to load the correct compilers.  The env file is always loaded from
# $GFDL_BASE and not the checked out git repo.

cb.compile()  # compile the source code to working directory $GFDL_WORK/codebase

# create an Experiment object to handle the configuration of model parameters
# and output diagnostics

exp_name = 'held_suarez_default_dann_stephen' #name of folder for experiment, so can be changed
exp = Experiment(exp_name, codebase=cb)

#Tell model how to write diagnostics, each line creates a new file. 
diag = DiagTable()
diag.add_file('atmos_monthly', 30, 'days', time_units='days') # time averaging. 
diag.add_file('atmos_monthly_1', 1, 'months', time_units='days') # in principal this would work, if month exists. 

# there is an ability to do spatial averaging if needs be.

#Tell model which diagnostics to write
diag.add_field('dynamics', 'ps', time_avg=True) # 'dynamics' refers to variables that come out of the dynamical core. Some other variables will come from the various radiation scheme. 
diag.add_field('dynamics', 'bk')# you can add a flag here to output the variable to either daily or monthly or other, defined in diag.add_file. 
diag.add_field('dynamics', 'pk',files = ['atmos_monthly']) # flag is files, e.g. files = ['atmos_monthly']
diag.add_field('dynamics', 'ucomp', time_avg=True)
diag.add_field('dynamics', 'vcomp', time_avg=True)
diag.add_field('dynamics', 'temp', time_avg=True)
diag.add_field('dynamics', 'vor', time_avg=True)
diag.add_field('dynamics', 'div', time_avg=True)
diag.add_field('hs_forcing', 'teq', time_avg=True)

exp.diag_table = diag

# define namelist values as python dictionary
# wrapped as a namelist object.
namelist = Namelist({
    'main_nml': {
        'dt_atmos': 600, # units of seconds. Will need to change if I change the spatial resolution, or rotation rate, or insolation. Check stability of winds with changing time step. 
        'days': 30,
        'calendar': 'thirty_day',
        'current_date': [2000,1,1,0,0,0] # doesn't matter for the model, but is important for things like Pandas. 
    },

    'atmosphere_nml': {
        'idealized_moist_model': False  # False for Newtonian Cooling.  True for Isca (Frierson == gray radiation).
    },

    'spectral_dynamics_nml': { # this is linked to the spatial resolition. 
        'damping_order'           : 4,                      # default: 2
        'water_correction_limit'  : 200.e2,                 # default: 0
        'reference_sea_level_press': 1.0e5,                  # default: 101325
        'valid_range_t'           : [100., 800.],           # default: (100, 500)
        'initial_sphum'           : 0.0,                  # default: 0
        'vert_coord_option'       : 'uneven_sigma',         # default: 'even_sigma'
        'scale_heights': 6.0, # highest pressure level = sur_p x e*scale_heights
        'exponent': 7.5, #don't worry too much - talk to Stephen if worried!
        'surf_res': 0.5 # ditto
    },

    # configure the relaxation profile
    'hs_forcing_nml': {
        't_zero': 315.,    # temperature at reference pressure at equator (default 315K)
        't_strat': 200.,   # stratosphere temperature (default 200K)
        'delh': 60.,       # equator-pole temp gradient (default 60K)
        'delv': 10.,       # lapse rate (default 10K)
        'eps': 0.,         # stratospheric latitudinal variation (default 0K)
        'sigma_b': 0.7,    # boundary layer friction height (default p/ps = sigma = 0.7)

        # negative sign is a flag indicating that the units are days
        'ka':   -40.,      # Constant Newtonian cooling timescale (default 40 days)
        'ks':    -4.,      # Boundary layer dependent cooling timescale (default 4 days)
        'kf':   -1.,       # BL momentum frictional timescale (default 1 days)

        'do_conserve_energy':   True,  # convert dissipated momentum into heat (default True)
    },

    'diag_manager_nml': {
        'mix_snapshot_average_fields': False
    },

    'fms_nml': {
        'domains_stack_size': 600000                        # default: 0
    },

    'fms_io_nml': {
        'threading_write': 'single',                         # default: multi
        'fileset_write': 'single',                           # default: multi
    }
})

exp.namelist = namelist
exp.set_resolution(*RESOLUTION)

#Lets do a run!
if __name__ == '__main__':
    exp.run(1, num_cores=NCORES, use_restart=False) # first month is run seperetly to not expect restart file. 
    for i in range(2, 13): # do twelve lots of 30 days
        exp.run(i, num_cores=NCORES)  # use the restart i-1 by default
