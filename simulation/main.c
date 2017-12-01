#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef double real_T;
typedef double time_T;
typedef unsigned char boolean_T;
typedef int int_T;
typedef unsigned int uint_T;
typedef unsigned long ulong_T;
typedef char char_T;
typedef unsigned char uchar_T;
typedef char_T byte_T;

#define false                       (0U)
#define true                        (1U)

#define DATA_PATH "heat_exchanger_data.txt"

/* Forward declaration for rtModel */
typedef struct tag_RTM_heat_exchanger_T RT_MODEL_heat_exchanger_T;

/* Block states (auto storage) for system '<Root>' */
typedef struct {
    real_T t_pm_state;
    real_T t_zco_state;
} DW_heat_exchanger_T;

/* External inputs (root inport signals with auto storage) */
typedef struct {
    real_T F_zm;
    real_T T_zm;
    real_T T_pco;
    real_T F_zco;                       
} ExtU_heat_exchanger_T;

/* External outputs (root outports fed by signals with auto storage) */
typedef struct {
    real_T t_pm;
    real_T t_zco;
} ExtY_heat_exchanger_T;

/* Block states (auto storage) */
DW_heat_exchanger_T heat_exchanger_DW;
/* External inputs (root inport signals with auto storage) */
ExtU_heat_exchanger_T heat_exchanger_U;
/* External outputs (root outports fed by signals with auto storage) */
ExtY_heat_exchanger_T heat_exchanger_Y;
real_T diff_gain;

/* Model step function */
static void heat_exchanger_step(void) {
    heat_exchanger_Y.t_pm = heat_exchanger_DW.t_pm_state;
    heat_exchanger_Y.t_zco = heat_exchanger_DW.t_zco_state;
    
    diff_gain = (heat_exchanger_DW.t_pm_state - heat_exchanger_DW.t_zco_state) * 250000.0;
    // Generate output state
    heat_exchanger_DW.t_pm_state += ((heat_exchanger_U.T_zm - heat_exchanger_DW.t_pm_state) * heat_exchanger_U.F_zm * 4.2E+6 - diff_gain) * 1.234567901234568E-7 * 0.5;
    heat_exchanger_DW.t_zco_state += (diff_gain - (heat_exchanger_DW.t_zco_state - heat_exchanger_U.T_pco) * heat_exchanger_U.F_zco * 4.2E+6) * 1.234567901234568E-7 * 0.5;
}

static void heat_exchanger_initialize_cold(void) {
    /* Initialize inputs */
    memset((void *)&heat_exchanger_U, 0, sizeof(ExtU_heat_exchanger_T));
    heat_exchanger_U.F_zco = 0.035;
    heat_exchanger_U.F_zm  = 0.015;
    heat_exchanger_U.T_pco = 50 + 273;
    heat_exchanger_U.T_zm  = 70 + 273;
    /* Reset outputs */
    memset((void *)&heat_exchanger_Y, 0,sizeof(ExtY_heat_exchanger_T));
    /* Initialize t_pm and t_zco - initial room temperature*/
    memset((void *)&heat_exchanger_DW, 0, sizeof(DW_heat_exchanger_T));
    heat_exchanger_DW.t_pm_state = 15.0 + 273;
    heat_exchanger_DW.t_zco_state = 15.0 + 273;
}

void half_second_step(void){
    /* Step the model */
    heat_exchanger_step();
    /* Print model outputs here */
    printf("State: %lf %lf\n", heat_exchanger_DW.t_pm_state, heat_exchanger_DW.t_zco_state);
}

static void save_heat_exchanger_state(FILE *sim_data) {
    fprintf(sim_data,"%3.5lf\n%3.5lf\n%3.5lf\n%3.5lf\n%3.5lf\n%3.5lf\n",
            heat_exchanger_U.F_zco,
            heat_exchanger_U.F_zm,
            heat_exchanger_U.T_pco,
            heat_exchanger_U.T_zm,
            heat_exchanger_DW.t_pm_state,
            heat_exchanger_DW.t_zco_state);
    printf("Data saved\n");
}

static void read_heat_exchanger_state(FILE *sim_data) {
    fscanf(sim_data, "%lf\n%lf\n%lf\n%lf\n%lf\n%lf\n",
            &heat_exchanger_U.F_zco,
            &heat_exchanger_U.F_zm,
            &heat_exchanger_U.T_pco,
            &heat_exchanger_U.T_zm,
            &heat_exchanger_DW.t_pm_state,
            &heat_exchanger_DW.t_zco_state);
    printf("Previous data loaded\n");
}



int main(int argc, const char * argv[]) {
    if(argc != 2) {
        printf("Wrong arguments!\n");
        return -1;
    }
    FILE *sim_data = fopen(DATA_PATH, "r");
    long sim_time = strtol(argv[1], NULL, 10);
    
    if (!sim_data) {
        printf("Creating new heat exchanger data file\n");
        sim_data = fopen(DATA_PATH, "w");
        if (!sim_data) {
            printf("Zjebalo sie :(\n");
            return -2;
        } else {
            heat_exchanger_initialize_cold();
        }
    } else {
        read_heat_exchanger_state(sim_data);
        fclose(sim_data);
        sim_data = fopen(DATA_PATH, "w");
        if (!sim_data) {
            printf("Zjebalo sie :(\n");
            return -2;
        }
    }
    printf("Starting from: %lf %lf\n", heat_exchanger_DW.t_pm_state, heat_exchanger_DW.t_zco_state);
    for (int i = 0; i < 2 * sim_time; i++) {
        half_second_step();
    }
    save_heat_exchanger_state(sim_data);
    fclose(sim_data);
    printf("End values: %lf %lf\n", heat_exchanger_DW.t_pm_state, heat_exchanger_DW.t_zco_state);
    return 0;
}
