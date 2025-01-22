import pandas as pd
import argparse
import numpy as np
import json

def main():
    parser = argparse.ArgumentParser(description='Convert the BrainSwipes CSV results file to a TSV file following HBCD specs.')
    parser.add_argument('input_csv', type=str, help='Path to the input CSV file')
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)

    with open('modalities.json', 'r') as file:
        mods = json.load(file)
    
    smri = mods['smri']
    fmri = mods['fmri']

    # Create smri DataFrame
    df_smri = pd.DataFrame()
    ## Patient ID, Sub ID, Run
    df_smri['participant_id'] = df['sample'].str.split('_').str[0]
    df_smri['session_id'] = df['sample'].str.split('_').str[1]
    df_smri['run_id'] = df['sample'].str.split('_').str[2]

    ## Temporary columns
    df_smri['temp_mean'] = df['aveVote']
    df_smri['temp_nrev'] = df['count']
    df_smri['temp_mod'] = df['sample'].str.split('_').str[4] + '_' + df['sample'].str.split('_').str[5]

    # Filter out func rows
    df_smri = df_smri[df_smri['run_id'].str.contains('run')]

    # Filter for each modality type and merge to output df
    df_merge = pd.DataFrame(columns=["participant_id", "session_id", "run_id"])
    for mod in smri:
        df_filt = df_smri[df_smri['temp_mod'].str.contains(mod)]
        df_filt = df_filt.drop('temp_mod', axis=1)
        df_filt.rename(columns={"temp_mean": f"{mod}_mean"}, inplace=True)
        df_filt.rename(columns={"temp_nrev": f"{mod}_nrev"}, inplace=True)

        # Insert new QC column for cleaner column ordering
        df_filt[f"{mod}_QC"]=np.nan

        df_merge=pd.merge(df_merge, df_filt, on=["participant_id", "session_id", "run_id"], how="outer")

    # Adjust values after merging
    for index, row in df_merge.iterrows():
        for mod in smri:
        # Set nrev to 0 if NaN 
            if pd.isna(row[f"{mod}_nrev"]):
                df_merge.at[index, f"{mod}_nrev"] = 0

        # Determine QC column values
            if row[f"{mod}_nrev"] < 10:
                df_merge[f"{mod}_QC"] = np.nan # Incomplete
            elif row[f"{mod}_mean"] < 0.7:
                df_merge[f"{mod}_QC"] = 0 # Fail
            elif row[f"{mod}_mean"] >= 0.7:
                 df_merge[f"{mod}_QC"] = 1 # Pass

    # Fill values for T1w_QC and T2w_QC - take sum of all QC columns - should be equal to 9 if passing and assigned value of 1. otherwise will be assigned 0 (Fail) or NaN if NaNs were present in columns sum was derived from 
    t1w_qc_columns = [col for col in df_merge.columns if "T1w_QC" in col]
    t2w_qc_columns = [col for col in df_merge.columns if "T2w_QC" in col]
    df_merge['T1w_QC_Sum'] = df_merge[t1w_qc_columns].sum(axis=1, skipna=False) # include NaNs
    df_merge['T2w_QC_Sum'] = df_merge[t2w_qc_columns].sum(axis=1, skipna=False) 
    df_merge['T1w_QC'] = np.where(df_merge['T1w_QC_Sum'].isna(), np.nan, (df_merge['T1w_QC_Sum'] == 9).astype(int))
    df_merge['T2w_QC'] = np.where(df_merge['T2w_QC_Sum'].isna(), np.nan, (df_merge['T2w_QC_Sum'] == 9).astype(int))

    # Drop sum columns and save 
    df_merge = df_merge.drop(['T1w_QC_Sum', 'T2w_QC_Sum'], axis=1)
    df_merge.to_csv('img_brainswipes_smri.tsv', index=None, na_rep='NaN', sep='\t')

    # FMRI
    # Create fmri DataFrame
    df_fmri = pd.DataFrame()
    ## Patient ID, Sub ID, Run
    df_fmri['participant_id'] = df['sample'].str.split('_').str[0]
    df_fmri['session_id'] = df['sample'].str.split('_').str[1]
    df_fmri['run_id'] = df['sample'].str.split('_').str[4]

    ## Temporary columns
    df_fmri['temp_mean'] = df['aveVote']
    df_fmri['temp_nrev'] = df['count']
    df_fmri['temp_mod'] = df['sample'].str.split('_').str[6] + '_' + df['sample'].str.split('_').str[7]

    # Filter out anat rows
    df_fmri = df_fmri[df_fmri['run_id'].str.contains('run')]

    # Filter for each modality type and merge to output df
    df_merge = pd.DataFrame(columns=["participant_id", "session_id", "run_id"])
    for mod in fmri:
        df_filt = df_fmri[df_fmri['temp_mod'].str.contains(mod)]
        df_filt = df_filt.drop('temp_mod', axis=1)
        df_filt.rename(columns={"temp_mean": f"{mod}_mean"}, inplace=True)
        df_filt.rename(columns={"temp_nrev": f"{mod}_nrev"}, inplace=True)

        # Insert new QC column for cleaner column ordering
        df_filt[f"{mod}_QC"]=np.nan

        df_merge=pd.merge(df_merge, df_filt, on=["participant_id", "session_id", "run_id"], how="outer")

    # Adjust values after merging
    for index, row in df_merge.iterrows():
        for mod in fmri:
        # Set nrev to 0 if NaN 
            if pd.isna(row[f"{mod}_nrev"]):
                df_merge.at[index, f"{mod}_nrev"] = 0

        # Determine QC column values
            if row[f"{mod}_nrev"] < 10:
                df_merge[f"{mod}_QC"] = np.nan # Incomplete
            elif row[f"{mod}_mean"] < 0.7:
                df_merge[f"{mod}_QC"] = 0 # Fail
            elif row[f"{mod}_mean"] >= 0.7:
                 df_merge[f"{mod}_QC"] = 1 # Pass

    # Fill values for fMRI_ref-T1w_QC and fMRI_ref-T2w_QC - take sum of all QC columns - should be equal to 2 if passing and assigned value of 1. otherwise will be assigned 0 (Fail) or NaN if NaNs were present in columns sum was derived from 
    t1w_qc_columns = [col for col in df_merge.columns if "T1w" and "QC" in col]
    t2w_qc_columns = [col for col in df_merge.columns if "T2w" and "QC" in col]
    df_merge['T1w_QC_Sum'] = df_merge[t1w_qc_columns].sum(axis=1, skipna=False) # include NaNs
    df_merge['T2w_QC_Sum'] = df_merge[t2w_qc_columns].sum(axis=1, skipna=False) 
    df_merge['fMRI_ref-T1w_QC'] = np.where(df_merge['T1w_QC_Sum'].isna(), np.nan, (df_merge['T1w_QC_Sum'] == 2).astype(int))
    df_merge['fMRI_ref-T2w_QC'] = np.where(df_merge['T2w_QC_Sum'].isna(), np.nan, (df_merge['T2w_QC_Sum'] == 2).astype(int))

    # Drop sum columns and save 
    df_merge = df_merge.drop(['T1w_QC_Sum', 'T2w_QC_Sum'], axis=1)
    df_merge.to_csv('img_brainswipes_fmri.tsv', index=None, na_rep='NaN', sep='\t')
            
if __name__ == "__main__":
    main()