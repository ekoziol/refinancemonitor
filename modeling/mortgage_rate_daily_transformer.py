import typer
import pandas as pd

app = typer.Typer()


@app.command()
def convert(fin: str, fout: str):
    df = pd.read_csv(fin)
    dfm = pd.melt(df, id_vars=['Date'], var_name='type', value_name='rate')
    dfm.to_csv(fout, index=False)
    return fout


if __name__ == '__main__':
    app()
