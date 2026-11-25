import pytest
from mongoengine.errors import ValidationError

from DAL.models import Discipline


def make_discipline(workload):
    return Discipline(id=7171, name="Disciplina sintética", course=[68], workload=workload)


@pytest.mark.parametrize("workload", [10, 20, 60])
def test_supported_workloads_validate_without_database(workload):
    make_discipline(workload).validate()


def test_workload_below_ten_is_rejected_without_database():
    with pytest.raises(ValidationError):
        make_discipline(9).validate()
