"""
Alpha Independence Analysis
==========================
Statistical testing framework to assess independence between alpha signals.
"""

import pandas as pd
import numpy as np
import os
from scipy.stats import pearsonr, spearmanr, kendalltau
from sklearn.feature_selection import mutual_info_regression
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.linear_model import LassoCV
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import grangercausalitytests
import warnings
warnings.filterwarnings('ignore')

# ==================== INDEPENDENCE TESTING ====================

def test_pairwise_independence(signal_A, signal_B, name_A='A', name_B='B'):
    """
    Comprehensive independence testing between two signals.
    
    Returns:
        dict with test statistics and independence decision
    """
    # Remove NaN values
    valid_idx = ~(np.isnan(signal_A) | np.isnan(signal_B))
    sig_A = signal_A[valid_idx]
    sig_B = signal_B[valid_idx]
    
    if len(sig_A) < 30:
        return None
    
    results = {
        'pair': f"{name_A} vs {name_B}",
        'n_samples': len(sig_A)
    }
    
    try:
        # 1. Pearson Correlation (linear dependency)
        results['pearson_r'], results['pearson_p'] = pearsonr(sig_A, sig_B)
        
        # 2. Spearman Correlation (monotonic dependency)
        results['spearman_r'], results['spearman_p'] = spearmanr(sig_A, sig_B)
        
        # 3. Kendall Tau (ordinal association)
        results['kendall_tau'], results['kendall_p'] = kendalltau(sig_A, sig_B)
        
        # 4. Mutual Information (general dependency)
        results['mutual_info'] = mutual_info_regression(
            sig_A.reshape(-1, 1), 
            sig_B,
            random_state=42
        )[0]
        
        # 5. Independence Decision
        alpha = 0.05
        results['independent'] = (
            abs(results['pearson_r']) < 0.3 and 
            results['pearson_p'] > alpha and
            results['mutual_info'] < 0.1
        )
        
        results['corr_level'] = (
            'High' if abs(results['pearson_r']) > 0.5 else
            'Moderate' if abs(results['pearson_r']) > 0.3 else
            'Low'
        )
        
    except Exception as e:
        print(f"Error testing {name_A} vs {name_B}: {e}")
        return None
    
    return results


def compute_correlation_matrix(signals_dict):
    """
    Compute correlation matrix for all alpha signals.
    
    Args:
        signals_dict: {alpha_name: DataFrame}
    
    Returns:
        DataFrame: Correlation matrix
    """
    # Stack all signals
    all_signals = []
    names = []
    
    for name, signal_df in signals_dict.items():
        # Flatten the signal (average across all tickers)
        signal_avg = signal_df.mean(axis=1)
        all_signals.append(signal_avg)
        names.append(name)
    
    # Create DataFrame
    df = pd.DataFrame({name: sig for name, sig in zip(names, all_signals)})
    
    # Compute correlation
    corr_matrix = df.corr()
    
    return corr_matrix


def calculate_vif(df_signals):
    """
    Calculate Variance Inflation Factor for multicollinearity detection.
    
    VIF > 5: Problematic
    VIF > 10: Severe multicollinearity
    """
    # Remove NaN
    df_clean = df_signals.dropna()
    
    if len(df_clean) < 50:
        return None
    
    vif_data = pd.DataFrame()
    vif_data['feature'] = df_clean.columns
    
    vif_scores = []
    for i in range(len(df_clean.columns)):
        try:
            vif = variance_inflation_factor(df_clean.values, i)
            vif_scores.append(vif)
        except:
            vif_scores.append(np.nan)
    
    vif_data['VIF'] = vif_scores
    vif_data['Status'] = vif_data['VIF'].apply(
        lambda x: 'Severe' if x > 10 else 'Problem' if x > 5 else 'OK' if x > 0 else 'N/A'
    )
    
    return vif_data


def run_pca_analysis(df_signals):
    """
    Principal Component Analysis to assess dimensionality.
    """
    # Remove NaN
    df_clean = df_signals.dropna()
    
    if len(df_clean) < 50:
        return None
    
    # Standardize
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    signals_scaled = scaler.fit_transform(df_clean)
    
    # PCA
    pca = PCA(n_components=len(df_clean.columns))
    pca.fit(signals_scaled)
    
    results = {
        'explained_variance': pca.explained_variance_ratio_,
        'cumulative_variance': np.cumsum(pca.explained_variance_ratio_),
        'components': pca.components_,
        'n_components_90': np.argmax(np.cumsum(pca.explained_variance_ratio_) >= 0.9) + 1
    }
    
    return results


def run_factor_analysis(df_signals, n_factors=3):
    """
    Factor Analysis to identify underlying factors.
    """
    # Remove NaN
    df_clean = df_signals.dropna()
    
    if len(df_clean) < 50:
        return None
    
    # Standardize
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    signals_scaled = scaler.fit_transform(df_clean)
    
    # Factor Analysis
    fa = FactorAnalysis(n_components=n_factors, random_state=42)
    fa.fit(signals_scaled)
    
    # Loadings
    loadings = pd.DataFrame(
        fa.components_.T,
        index=df_clean.columns,
        columns=[f'Factor{i+1}' for i in range(n_factors)]
    )
    
    return {
        'loadings': loadings,
        'noise_variance': fa.noise_variance_
    }


# ==================== FEATURE SELECTION ====================

def greedy_forward_selection(signals_dict, target, max_correlation=0.5):
    """
    Greedy forward selection based on IC and correlation.
    
    Args:
        signals_dict: {alpha_name: DataFrame}
        target: Forward returns
        max_correlation: Maximum allowed correlation between selected alphas
    
    Returns:
        list: Selected alpha names
    """
    # Compute IC for each alpha
    ic_scores = {}
    for name, signal_df in signals_dict.items():
        # Calculate IC (average correlation with forward return)
        signal_flat = signal_df.stack()
        target_flat = target.stack()
        
        # Align
        common_idx = signal_flat.index.intersection(target_flat.index)
        if len(common_idx) < 100:
            continue
        
        sig = signal_flat.loc[common_idx]
        tgt = target_flat.loc[common_idx]
        
        # Remove NaN
        valid = ~(sig.isna() | tgt.isna())
        if valid.sum() < 100:
            continue
        
        ic, _ = spearmanr(sig[valid], tgt[valid])
        ic_scores[name] = abs(ic)
    
    # Start with highest IC
    selected = [max(ic_scores, key=ic_scores.get)]
    print(f"Starting with: {selected[0]} (IC: {ic_scores[selected[0]]:.4f})")
    
    # Greedy addition
    for alpha in sorted(ic_scores.keys(), key=lambda x: ic_scores[x], reverse=True):
        if alpha in selected:
            continue
        
        # Check correlation with already selected
        max_corr = 0
        for selected_alpha in selected:
            sig_a = signals_dict[alpha].mean(axis=1)
            sig_s = signals_dict[selected_alpha].mean(axis=1)
            
            valid = ~(sig_a.isna() | sig_s.isna())
            if valid.sum() < 50:
                continue
            
            corr, _ = pearsonr(sig_a[valid], sig_s[valid])
            max_corr = max(max_corr, abs(corr))
        
        if max_corr < max_correlation:
            selected.append(alpha)
            print(f"Added: {alpha} (IC: {ic_scores[alpha]:.4f}, Max Corr: {max_corr:.3f})")
        else:
            print(f"Rejected: {alpha} (IC: {ic_scores[alpha]:.4f}, Max Corr: {max_corr:.3f} > {max_correlation})")
    
    return selected


def lasso_feature_selection(signals_dict, target, cv=5):
    """
    LASSO-based automatic feature selection.
    """
    # Prepare data
    signal_list = []
    names = []
    
    for name, signal_df in signals_dict.items():
        signal_flat = signal_df.stack()
        signal_list.append(signal_flat)
        names.append(name)
    
    target_flat = target.stack()
    
    # Align all
    common_idx = target_flat.index
    for sig in signal_list:
        common_idx = common_idx.intersection(sig.index)
    
    X = pd.DataFrame({
        name: sig.loc[common_idx] 
        for name, sig in zip(names, signal_list)
    }).dropna()
    
    y = target_flat.loc[X.index]
    
    if len(X) < 100:
        return names  # Return all if not enough data
    
    # LASSO with cross-validation
    lasso = LassoCV(cv=cv, alphas=np.logspace(-4, 1, 50), random_state=42, max_iter=5000)
    lasso.fit(X, y)
    
    # Selected features
    selected_idx = np.where(lasso.coef_ != 0)[0]
    selected = [names[i] for i in selected_idx]
    
    print(f"LASSO selected {len(selected)}/{len(names)} alphas")
    print(f"Coefficients: {dict(zip(names, lasso.coef_))}")
    
    return selected


# ==================== MAIN ANALYSIS ====================

def analyze_alpha_independence(results_dir, output_dir=None):
    """
    Complete independence analysis of alpha signals.
    """
    if output_dir is None:
        output_dir = results_dir
    
    print("="*60)
    print("ALPHA INDEPENDENCE ANALYSIS")
    print("="*60)
    
    # Load all signal files
    signals_dict = {}
    for file in os.listdir(results_dir):
        if file.startswith('signals_cluster_'):
            cluster = file.replace('signals_cluster_', '').replace('.csv', '')
            df = pd.read_csv(
                os.path.join(results_dir, file),
                index_col=0,
                parse_dates=True
            )
            
            # Extract individual alpha signals (average across tickers)
            for alpha in ['MR', 'Mom', 'VB', 'XSR', 'Val']:
                alpha_cols = [col for col in df.columns if col.startswith(f'{alpha}_')]
                if alpha_cols:
                    if alpha not in signals_dict:
                        signals_dict[alpha] = []
                    signals_dict[alpha].append(df[alpha_cols].mean(axis=1))
    
    # Average across all clusters
    for alpha in signals_dict:
        signals_dict[alpha] = pd.concat(signals_dict[alpha], axis=1).mean(axis=1)
    
    print(f"\nLoaded {len(signals_dict)} alpha signals")
    
    # 1. Correlation Matrix
    print("\n" + "="*60)
    print("1. CORRELATION MATRIX")
    print("="*60)
    
    df_signals = pd.DataFrame(signals_dict)
    corr_matrix = df_signals.corr()
    print(corr_matrix.round(3))
    
    # 2. Pairwise Independence Tests
    print("\n" + "="*60)
    print("2. PAIRWISE INDEPENDENCE TESTS")
    print("="*60)
    
    alpha_names = list(signals_dict.keys())
    independence_results = []
    
    for i, alpha1 in enumerate(alpha_names):
        for j, alpha2 in enumerate(alpha_names[i+1:], start=i+1):
            result = test_pairwise_independence(
                signals_dict[alpha1].values,
                signals_dict[alpha2].values,
                alpha1, alpha2
            )
            if result:
                independence_results.append(result)
                print(f"\n{result['pair']}:")
                print(f"  Pearson r:  {result['pearson_r']:7.3f} (p={result['pearson_p']:.4f})")
                print(f"  Spearman ρ: {result['spearman_r']:7.3f} (p={result['spearman_p']:.4f})")
                print(f"  Mutual Info: {result['mutual_info']:6.3f}")
                print(f"  Correlation: {result['corr_level']}")
                print(f"  Independent: {result['independent']}")
    
    # 3. VIF Analysis
    print("\n" + "="*60)
    print("3. VARIANCE INFLATION FACTOR (VIF)")
    print("="*60)
    
    vif_data = calculate_vif(df_signals)
    if vif_data is not None:
        print(vif_data.to_string(index=False))
    
    # 4. PCA Analysis
    print("\n" + "="*60)
    print("4. PRINCIPAL COMPONENT ANALYSIS")
    print("="*60)
    
    pca_results = run_pca_analysis(df_signals)
    if pca_results:
        print("Explained Variance Ratio:")
        for i, var in enumerate(pca_results['explained_variance']):
            cum_var = pca_results['cumulative_variance'][i]
            print(f"  PC{i+1}: {var:.3f} (Cumulative: {cum_var:.3f})")
        print(f"\nComponents needed for 90% variance: {pca_results['n_components_90']}")
    
    # 5. Factor Analysis
    print("\n" + "="*60)
    print("5. FACTOR ANALYSIS")
    print("="*60)
    
    fa_results = run_factor_analysis(df_signals, n_factors=3)
    if fa_results:
        print("Factor Loadings:")
        print(fa_results['loadings'].round(3))
    
    # Save results
    results_summary = {
        'correlation_matrix': corr_matrix,
        'independence_tests': pd.DataFrame(independence_results),
        'vif': vif_data,
        'pca': pca_results,
        'factor_analysis': fa_results
    }
    
    # Save to CSV
    corr_matrix.to_csv(os.path.join(output_dir, 'alpha_correlation_matrix.csv'))
    if vif_data is not None:
        vif_data.to_csv(os.path.join(output_dir, 'alpha_vif_scores.csv'), index=False)
    pd.DataFrame(independence_results).to_csv(
        os.path.join(output_dir, 'alpha_independence_tests.csv'),
        index=False
    )
    
    print(f"\n✅ Results saved to {output_dir}")
    
    return results_summary


if __name__ == "__main__":
    results_dir = '/home/tiencd123456/CF_Tien23280088_Hoang23280060-1/project/apply_strategy/MultiAlpha_Results'
    
    results = analyze_alpha_independence(results_dir)
