import time

from rest_api.utils import create_foreign_key_hashmap, log


def process_model_rows(chunk, id_set, model, use_internal_id, project_pk):
    to_create = list()
    to_update = list()

    if use_internal_id:
        internal_id = model.objects.get_internal_id_name()
        id_map = create_foreign_key_hashmap(chunk, model, project_pk, internal_id, internal_id)

        for idx, row in enumerate(chunk):
            # We store the internal ID so we don't delete the entries afterwards
            id_set.add(row[internal_id])
            if row[internal_id] in id_map:
                row['id'] = id_map[row[internal_id]]
            # Create a model but don't save it! we don't want to perform one SQL operation per entry
            obj = model(**row)
            # if the row already existed we prepare it for updating
            if row[internal_id] in id_map:
                to_update.append(obj)
            # otherwise we prepare it for creation
            else:
                to_create.append(obj)
    else:
        to_create.extend(list(map(lambda r: model(**r), chunk)))

    return to_create, to_update


def create_and_update_chunk(to_create, to_update, params, model, use_internal_id, batch_size=1000):
    if not to_create and not to_update:
        return
    t0 = time.time()
    model.objects.bulk_create(to_create, batch_size=batch_size)
    t1 = time.time()
    log(f"Created {len(to_create)} records in {t1 - t0:.5f} seconds")
    if use_internal_id:
        model.objects.bulk_update(to_update, params, batch_size=batch_size)
        t2 = time.time()
        log(f"Updated {len(to_update)} records in {t2 - t1:.5f} seconds")
