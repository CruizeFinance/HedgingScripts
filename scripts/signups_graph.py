import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('/Users/prithvirajmurthy/Desktop/blockchain/cruize/scripts/scripts/v4.csv')
print(df)

signup_dates = df["Signup date"].values.tolist()
# signup_dates
wallets = df["Crypo wallet address"].values.tolist()
# wallets

xpoints = np.array(signup_dates)
ypoints = np.array(wallets)

plt.ylim(0, 200)
plt.xlim(0, 100)

plt.ylabel("Wallets")
plt.xlabel("Signup Dates")

plt.plot(xpoints, ypoints)
# plt.vlines(
#     x=70,
#     ymin=0,
#     ymax=200,
#     colors="red",
#     label='Signups and Wallets',
# )
# plt.legend()
plt.show()