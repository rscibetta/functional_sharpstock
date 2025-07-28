import streamlit as st
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple

class ABTestingFramework:
    def __init__(self, alpha=0.05, power=0.8):
        self.alpha = alpha  # Significance level
        self.power = power  # Statistical power
        self.beta = 1 - power  # Type II error rate
    
    def calculate_sample_size(self, effect_size: float, baseline_std: float) -> int:
        """Calculate required sample size for detecting effect"""
        # Cohen's d effect size
        cohens_d = effect_size / baseline_std
        
        # Z-scores for alpha and beta
        z_alpha = stats.norm.ppf(1 - self.alpha/2)  # Two-tailed
        z_beta = stats.norm.ppf(self.power)
        
        # Sample size calculation
        n = 2 * ((z_alpha + z_beta) / cohens_d) ** 2
        
        return int(np.ceil(n))
    
    def run_ab_test(self, control_group: List[float], 
                    treatment_group: List[float],
                    metric_name: str = "Performance") -> Dict:
        """Run A/B test comparing two groups"""
        
        # Descriptive statistics
        control_mean = np.mean(control_group)
        treatment_mean = np.mean(treatment_group)
        control_std = np.std(control_group, ddof=1)
        treatment_std = np.std(treatment_group, ddof=1)
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(control_group)-1)*control_std**2 + 
                             (len(treatment_group)-1)*treatment_std**2) / 
                            (len(control_group) + len(treatment_group) - 2))
        cohens_d = (treatment_mean - control_mean) / pooled_std
        
        # Statistical test
        t_stat, p_value = stats.ttest_ind(treatment_group, control_group)
        
        # Confidence interval for difference
        se_diff = pooled_std * np.sqrt(1/len(control_group) + 1/len(treatment_group))
        diff_mean = treatment_mean - control_mean
        margin_error = stats.t.ppf(1-self.alpha/2, 
                                  len(control_group)+len(treatment_group)-2) * se_diff
        ci_lower = diff_mean - margin_error
        ci_upper = diff_mean + margin_error
        
        # Results
        results = {
            'metric_name': metric_name,
            'control_mean': control_mean,
            'treatment_mean': treatment_mean,
            'difference': diff_mean,
            'percent_change': (diff_mean / control_mean * 100) if control_mean != 0 else 0,
            'cohens_d': cohens_d,
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < self.alpha,
            'confidence_interval': (ci_lower, ci_upper),
            'control_size': len(control_group),
            'treatment_size': len(treatment_group),
            'power_achieved': self._calculate_achieved_power(cohens_d, len(control_group), len(treatment_group))
        }
        
        return results
    
    def _calculate_achieved_power(self, cohens_d: float, n1: int, n2: int) -> float:
        """Calculate achieved statistical power"""
        # Non-centrality parameter
        ncp = cohens_d * np.sqrt((n1 * n2) / (n1 + n2)) * np.sqrt(2)
        
        # Critical t-value
        df = n1 + n2 - 2
        t_crit = stats.t.ppf(1 - self.alpha/2, df)
        
        # Power calculation
        power = 1 - stats.t.cdf(t_crit, df, ncp) + stats.t.cdf(-t_crit, df, ncp)
        
        return power
    
    def compare_algorithms(self, baseline_results: Dict[str, List[float]], 
                          new_algorithm_results: Dict[str, List[float]]) -> Dict:
        """Compare multiple metrics between algorithms"""
        comparison_results = {}
        
        for metric in baseline_results.keys():
            if metric in new_algorithm_results:
                test_result = self.run_ab_test(
                    baseline_results[metric],
                    new_algorithm_results[metric],
                    metric
                )
                comparison_results[metric] = test_result
        
        return comparison_results
