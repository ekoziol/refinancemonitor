# ML Experiment Setup

Create a new ML experiment for: $ARGUMENTS

## Experiment Setup Process

1. **Experiment Design**:
   - Define experiment objectives and hypotheses
   - Identify key metrics and success criteria
   - Plan data requirements and preprocessing steps
   - Consider baseline models for comparison

2. **Data Pipeline**:
   - Verify data availability and quality
   - Setup data preprocessing pipeline
   - Implement feature engineering if needed
   - Create data validation checks

3. **Model Development**:
   - Choose appropriate PyMC model architecture
   - Implement Bayesian model using PyMC 5.22.0
   - Set up proper priors and likelihood functions
   - Include uncertainty quantification

4. **Experiment Tracking**:
   - Setup MLflow experiment tracking
   - Log parameters, metrics, and artifacts
   - Version control model code and data
   - Document model assumptions and limitations

5. **Validation Strategy**:
   - Implement cross-validation or holdout validation
   - Create model diagnostics and convergence checks
   - Compare with baseline and existing models
   - Perform sensitivity analysis

6. **Jupyter Notebook**:
   - Create experiment notebook in `notebooks/`
   - Include clear documentation and markdown cells
   - Add visualizations for results interpretation
   - Ensure reproducibility with seed setting

## Experiment Structure

```
mmm_workbench/
├── notebooks/
│   └── experiment_$ARGUMENTS.ipynb
├── src/
│   ├── model/
│   │   └── $ARGUMENTS_model.py
│   └── utils/
│       └── $ARGUMENTS_utils.py
├── tests/
│   └── test_$ARGUMENTS.py
└── data/
    └── $ARGUMENTS/
```

## Quality Checklist

- [ ] Clear experiment objectives defined
- [ ] Data pipeline implemented and validated
- [ ] PyMC model properly specified
- [ ] MLflow tracking configured
- [ ] Model diagnostics included
- [ ] Jupyter notebook documented
- [ ] Tests written for model components
- [ ] Results interpretation provided
- [ ] Reproducibility ensured

## MLflow Integration

- Log experiment parameters and hyperparameters
- Track model performance metrics
- Save model artifacts and plots
- Document model assumptions and limitations
- Compare with baseline models

## Bayesian Modeling Best Practices

- Use informative priors when domain knowledge available
- Implement proper model diagnostics (R-hat, ESS)
- Include uncertainty quantification in predictions
- Validate model assumptions with posterior predictive checks
- Document convergence criteria and sampling parameters