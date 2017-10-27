%% differential equations' variables

%T_pm  -->  temperature of "out" water
%T_zco -->  temperature for AGH; when t_o -> T_zco = 273K

%% initial values

T_pm_0  = 15; 
T_zco_0 = 15;  % because when t_o -> T_zco = 0 C

%% parameters for heat exchanger

M_m   = 3000;       % kg  "+/-" value
M_co  = 3000;       % kg  "+/-" value
c_wym = 2700;       % J/kg/K
c_w   = 4200;       % J/kg/K
rho   = 1000;       % kg/m3
k_w   = 250000;     % J/s/K

%% other variables

F_zm = 0.015;       % hot water stream 0-0.0022 m3/s (it goes through controlled valve)
T_zm = 70;     % collected water's temperature 70-135 C; when t_o -> T_zm = 273K 
F_zco = 0.035;     % output stream for AGH 0-0.0042 m3/s
T_pco = 50;    % output temperature from AGH

%% running simulation model

sim('heat_exchanger');