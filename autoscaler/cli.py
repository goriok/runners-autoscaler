import click

from autoscaler import __version__, start_command


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.version_option(version=str(__version__.__version__))
@click.pass_context
def cli(ctx, debug) -> None:
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug


@cli.command('start', help="Starts Kubernetes controller.")
@click.pass_context
def start(ctx):
    start_command.main()


def main() -> None:
    # pylint: disable=no-value-for-parameter
    cli(obj={})


if __name__ == '__main__':
    main()
