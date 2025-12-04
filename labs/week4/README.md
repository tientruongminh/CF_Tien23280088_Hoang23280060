# Lab: Week 4

## 1. Handling outliers

This section we want to implement open-source models to unsupervised anomaly detection. Therefore, after having the results from the models, we only use simple method to handling such outliers, by droping all of those points.

The model we used is specify in this section, which called TimesNet: [Paper](https://arxiv.org/pdf/2210.02186). 

Below are some descriptions about the model we're going to use, the code for this section is notebooks/timesnet.ipynb

## 1.1. What is TimesNet

TimesNet (Wu et al., ICLR 2023) is a general-purpose backbone model for time-series analysis.  
Its core idea:

- Real-world time series often exhibit **multi-periodicity** (daily, weekly, yearly patterns).
- These patterns contain:
  - **Intraperiod variation** (within a single period)
  - **Interperiod variation** (variation across different periods)
- Instead of treating time series as 1D sequences, TimesNet **reshapes** a 1D series into **2D tensors**, where:
  - Columns capture intraperiod structure
  - Rows capture interperiod relationships

A “TimesBlock” module processes these 2D tensors using a multi-scale 2D Inception-style backbone.  
This allows TimesNet to explicitly model both types of variation.

TimesNet is positioned as a **general (foundation) model for time-series tasks**, including forecasting, imputation, classification and anomaly detection.

---

## 1.2. What Tasks TimesNet Can Be Used For

TimesNet is evaluated on five major categories of time-series tasks:

- **Short-term forecasting**  
  Predicting several steps ahead in the near future.

- **Long-term forecasting**  
  Predicting farther ahead for both univariate and multivariate series.

- **Imputation**  
  Filling missing values in partially observed time series.

- **Classification**  
  Assigning labels to entire time‐series segments.

- **Anomaly detection**  
  Detecting unusual segments in multivariate monitoring data.

Because the same architecture handles all these tasks, TimesNet acts as a versatile model suitable for most time-series applications.

---

## 1.3. How TimesNet Works (Key Technical Ideas)

### 1.3.1 Multi-Periodicity and 2D Transformation

Key steps:

1. Many time series contain multiple periodic frequencies.  
   Example: daily + weekly patterns in traffic, seasonal patterns in weather.

2. TimesNet computes **FFT** to identify the **top-k significant frequencies**.

3. For each discovered period  $p_i$ :
   - The original 1D series of length  $T$  is reshaped (with padding) into a **2D tensor** of size  
     
     $(p_i \times f_i)$
    
     where rows represent periods and columns represent within-period steps.

4. This 2D representation makes it possible to learn:
   - **Intraperiod structure** (within columns)
   - **Interperiod structure** (within rows)

### 1.3.2 TimesBlock and Feature Aggregation

A TimesBlock:

1. Takes the input 1D series.
2. Predicts relevant periods via FFT.
3. Reshapes into multiple 2D tensors.
4. Applies a **shared 2D multi-scale Inception block** (kernels like 3×3, 5×5, 7×7).
5. Flattens the results back into 1D.
6. Aggregates outputs from different periods using **softmax weights** based on FFT amplitudes.

Multiple TimesBlocks are stacked with residual connections.  
Because the inception module is shared, the number of parameters does not grow with \( k \).

### 1.3.3 Generality to Vision Backbones

After converting to a 2D representation, TimesNet can optionally use:

- ResNet
- ConvNext
- Other 2D CNN / vision architectures

The paper mainly uses a lightweight inception block for efficiency.

---

## 1.4. How Good Is It (Evaluation Summary)

TimesNet is tested across five task categories with strong results.

### Forecasting Performance

Benchmarked on:
- Long-term forecasting datasets: ETT, Electricity, Traffic, Weather, Exchange, ILI  
- Short-term forecasting (M4 dataset)

Examples:
- On **ETTm1**, TimesNet achieves **MSE ≈ 0.400**, outperforming ETSformer (0.429).
- On **M4 short-term forecasting**, TimesNet reports:  
  - SMAPE = **11.829**  
  - MASE = **1.585**  
  - OWA = **0.851**  
  outperforming N-HiTS and N-BEATS.

### Imputation, Classification, Anomaly Detection

Across imputation, classification and anomaly detection settings:
- TimesNet achieves **consistent state-of-the-art** results.

### Key Statements from Authors

- “TimesNet achieves consistent state-of-the-art performance on five mainstream analysis tasks.”
- Using stronger 2D backbones improves performance further, demonstrating architecture flexibility.

### Caveats

- Works best on data with periodic structure.
- Hyperparameter choices (k periods, embedding dimension) are important.
- Heavy 2D backbones increase computation cost.



## 2. Applying regression


