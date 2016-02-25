import subprocess
import click
import os
from distutils.version import StrictVersion
import shutil
import re


def get_version():
    p = get_version_file_path()
    with open(p) as f:
        version = f.read()
        version = version.strip()
        if not version:
            raise ValueError("could not read version")
        return version


def write_version(version_tuple):
    p = get_version_file_path()
    with open(p, 'w+') as f:
        f.write('.'.join([str(i) for i in version_tuple]))


def get_version_file_path():
    p = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'VERSION')
    return p


def release_patch(version_tuple):
    patch_version = version_tuple[2] + 1
    new_version = version_tuple[:2] + (patch_version,)
    click.echo('new version: %s' % str(new_version))
    write_version(new_version)
    return new_version


def release_minor(version_tuple):
    minor = version_tuple[1] + 1
    new_version = version_tuple[:1] + (minor, 0)
    click.echo('new version: %s' % str(new_version))
    write_version(new_version)
    return new_version


def release_major(version_tuple):
    major = version_tuple[0] + 1
    new = (major, 0, 0)
    click.echo('new version: %s' % str(new))
    write_version(new)
    return new


@click.command()
@click.option('--release', '-r', type=click.Choice(['major', 'minor', 'patch']), default='patch')
@click.option('--url', prompt=True, default=lambda: os.environ.get('FURY_URL', ''))
def main(release, url):
    version_tuple = StrictVersion(get_version()).version
    click.echo('old version: %s' % str(version_tuple))

    if release == 'major':
        new_v = release_major(version_tuple)
    elif release == 'minor':
        new_v = release_minor(version_tuple)
    else:
        new_v = release_patch(version_tuple)

    new_v_s = '.'.join([str(i) for i in new_v])

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.call("python setup.py sdist", shell=True)

    pkg_file = ''
    for f in os.listdir('dist'):
        r = re.compile(r'.*(%s\.tar\.gz)' % re.escape(new_v_s))
        result = r.match(f)
        if result:
            click.echo(f + ' is ready')
            pkg_file = f

            break

    if not pkg_file:
        raise ValueError

    this_folder = os.path.dirname(os.path.abspath(__file__))
    dist_folder = os.path.join(this_folder, 'dist')
    pkg_file_name = pkg_file
    pkg_file = os.path.join(dist_folder, pkg_file)

    shutil.move(pkg_file, this_folder)
    shutil.rmtree(dist_folder)
    os.remove('MANIFEST')
    is_release = click.confirm('ready to release?')

    if is_release:
        subprocess.call('curl -F package=@%s %s' % (pkg_file_name, url),
                        shell=True)
        os.remove(pkg_file_name)


if __name__ == '__main__':
    main()
