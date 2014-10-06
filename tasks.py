from invoke import Collection, task, run

from okcupyd import tasks


ns = Collection()
ns.add_collection(tasks, name='okcupyd')


@ns.add_task
@task(default=True)
def install():
    run("python setup.py install")


@ns.add_task
@task
def pypi():
    run("python setup.py sdist upload -r pypi")


@ns.add_task
@task(aliases='r')
def rerecord(rest):
    run('tox -e py27 -- --record --credentials test_credentials -k {0} -s'
        .format(rest))
    run('tox -e py27 -- --resave --scrub --credentials test_credentials -k {0} -s'
        .format(rest))


@ns.add_task
@task
def rerecord_failing():
    result = run("tox -e py27 | grep test_ | grep \u2015 | sed 's:\\\u2015::g'",
                 hide='out')
    for test_name in result.stdout.split('\n'):
        rerecord(rest='-k {0}'.format(test_name.strip()))
