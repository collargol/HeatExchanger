import time




# start counting time...
tic = time.time()

T_pm_0 = 15
T_zco_0 = 15

M_m = 3000      # kg  "+/-" value
M_co = 3000     # kg  "+/-" value
c_wym = 2700    # J/kg/K
c_w = 4200      # J/kg/K
rho = 1000      # kg/m3
k_w = 250000    # J/s/K

F_zm = 0.015        # 0-0.0022 m3/s
T_zm = 90
F_zco = 0.035       # 0-0.0042 m3/s
T_pco = 70

T_pm = []
T_pm.append(T_pm_0)
T_zco = []
T_zco.append(T_zco_0)

# creating time vector
time_period = 1000000   # 1000000 ms == 1000s
delta_t = 0.001
t = []
for ti in range(time_period):
    t.append(ti)

# calculation

for i in range(time_period - 1):
    T_zco.append(T_zco[i] + delta_t * (((-F_zm * rho * c_w) / (M_m * c_wym)) * (T_zco[i] - T_pco) + (k_w / (M_m * c_wym)) * (T_pm[i] - T_zco[i])))
    T_pm.append(T_pm[i] + delta_t * (((F_zm * rho * c_w) / (M_m * c_wym)) * (T_zm - T_pm[i]) + (-k_w / (M_m * c_wym)) * (T_pm[i] - T_zco[i])))
print(str(T_zco[len(T_zco) - 1]))
toc = time.time() - tic
print(str(toc))
"""
# drawing plot
plt.plot(t, T_pm, 'y', label='T_pm')
plt.plot(t, T_zco, 'b', label='T_zco')
plt.xlabel('Time [ms]')
plt.ylabel('Temperature [C]')
plt.legend(loc='lower right')
plt.grid(True)
plt.show() 
"""