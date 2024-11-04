import click
from yt_quicklook.sampling import sample_a_ds

@click.group()
def cli():
    pass


@cli.command()
@click.argument('sample_name')
@click.argument('output_dir')
def sample(sample_name, output_dir):
    print(f"generating {sample_name} quick look sample")
    sample_a_ds(sample_name, output_dir)

