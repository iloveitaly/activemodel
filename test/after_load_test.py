from sqlmodel import Field
from sqlalchemy.dialects.postgresql import JSONB

from activemodel import BaseModel




class AfterLoadModel(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = Field(default=None)
    latest_event: str | None = Field(default=None)

    def after_load(self):
        self.latest_event = f"after_load:{self.id}"

class AfterLoadModelWithSaveOnLoad(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = Field(default=None)
    latest_event: str | None = Field(default=None)

    def after_load(self):
        if not self.latest_event:
            self.latest_event = f"after_load:{self.id}"
            self.save()

def test_save_does_not_call_after_load(create_and_wipe_database):
    obj = AfterLoadModel(name="saved").save()
    assert obj.id is not None
    assert obj.latest_event is None

def test_after_load_called_on_get(create_and_wipe_database):
    obj = AfterLoadModel(name="loaded").save()
    assert obj.id is not None

    loaded = AfterLoadModel.get(obj.id)

    assert loaded is not None
    assert loaded.name == "loaded"
    assert loaded.latest_event == f"after_load:{obj.id}"


def test_after_load_called_on_query_wrapper_first(create_and_wipe_database):
    obj = AfterLoadModel(name="loaded2").save()
    assert obj.id is not None

    loaded = AfterLoadModel.where(AfterLoadModel.id == obj.id).first()

    assert loaded is not None
    assert loaded.id == obj.id
    assert loaded.latest_event == f"after_load:{obj.id}"


def test_after_load_called_on_refresh(create_and_wipe_database):
    obj = AfterLoadModel(name="refresh_me").save()
    assert obj.id is not None

    loaded = AfterLoadModel.get(obj.id)
    assert loaded is not None

    # Persist a change, then verify `refresh()` re-materializes the instance
    loaded.name = "refreshed"
    loaded.save()

    loaded.refresh()

    assert loaded.latest_event == f"after_load:{obj.id}"

def test_after_load_called_on_save(create_and_wipe_database):
    obj = AfterLoadModelWithSaveOnLoad(name="saved2").save()
    assert obj.id is not None
    assert obj.latest_event is None

    obj.refresh()
    assert obj.latest_event is not None
    assert obj.latest_event == f"after_load:{obj.id}"

def test_after_load_called_on_query_wrapper_all(create_and_wipe_database):
    obj = AfterLoadModelWithSaveOnLoad(name="loaded3").save()
    assert obj.id is not None

    loaded_list = list(AfterLoadModelWithSaveOnLoad.where(AfterLoadModelWithSaveOnLoad.id == obj.id).all())
    assert len(loaded_list) == 1
    assert loaded_list[0].id == obj.id
    assert loaded_list[0].latest_event == f"after_load:{obj.id}"
