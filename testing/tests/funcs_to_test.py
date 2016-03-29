from time import sleep

from django.db.models import F

from testapp.decorators import badly_decorated
from testapp.models import Semaphore


def update_count_naive(id_):
    try:
        obj = Semaphore.objects.get(pk=id_, locked=False)
    except Semaphore.DoesNotExist:
        return False

    sleep(0.1)  # make a nice race condition
    obj.locked = True
    obj.save()

    obj.count += 1
    obj.locked = False
    obj.save()
    return True


def update_count_transactional(id_):
    Semaphore.objects.filter(pk=id_, locked=False).update(count=F('count') + 1)
    return True


class CustomError(Exception):
    pass


def raise_exception():
    raise CustomError('WTF')


@badly_decorated
def wallpaper(colour):
    return '%s stripes' % colour
