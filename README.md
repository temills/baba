# Data, study materials, analysis code, and models for Baba is You study

## Computational models

To run the models:
```bash
python -m models.play
```

## Human experiment

This experiment uses Redis for game state. To run locally:
1. Start Redis:
```bash
brew services start redis
```
2. Run the experiment:
```bash
python -m human_experiment.app.run_local
```
3. When you are done, you can stop Redis:
```bash
brew services stop redis
```

## Analysis

All analyses in analysis/main.Rmd