from collections import defaultdict
import json
import re
import sys
from datetime import datetime
import string

from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.postgresql_backend.pg_connection_handler import PgConnectionHandlerService
from datastore.writer.app import register_services


def copy(obj, *attrs):
    return {attr: obj[attr] for attr in attrs if attr in obj}


PERMISSION_MAPPING = {
    "agenda_item.can_see": "agenda.can_see",
    "agenda_item.can_see_internal": "agenda.can_see_internal_items",
    "agenda_item.can_manage": "agenda.can_manage",
    "assignment.can_see": "assignments.can_see",
    "assignment.can_manage": "assignments.can_manage",
    "assignment.can_nominate_other": "assignments.can_nominate_other",
    "assignment.can_nominate_self": "assignments.can_nominate_self",
    "chat.can_manage": "chat.can_manage",
    "list_of_speakers.can_see": "agenda.can_see_list_of_speakers",
    "list_of_speakers.can_manage": "agenda.can_manage_list_of_speakers",
    "list_of_speakers.can_be_speaker": "agenda.can_be_speaker",
    "mediafile.can_see": "mediafiles.can_see",
    "mediafile.can_manage": "mediafiles.can_manage",
    "meeting.can_manage_settings": "core.can_manage_config",
    "meeting.can_manage_logos_and_fonts": "core.can_manage_logos_and_fonts",
    "meeting.can_see_frontpage": "core.can_see_frontpage",
    "meeting.can_see_autopilot": "core.can_see_autopilot",
    "meeting.can_see_livestream": "core.can_see_livestream",
    "meeting.can_see_history": "core.can_see_history",
    "motion.can_see": "motions.can_see",
    "motion.can_see_internal": "motions.can_see_internal",
    "motion.can_manage": "motions.can_manage",
    "motion.can_manage_metadata": "motions.can_manage_metadata",
    "motion.can_manage_polls": "motions.can_manage_polls",
    "motion.can_create": "motions.can_create",
    "motion.can_create_amendments": "motions.can_create_amendments",
    "motion.can_support": "motions.can_support",
    "projector.can_see": "core.can_see_projector",
    "projector.can_manage": "core.can_manage_projector",
    "projector.can_manage": "core.can_manage_tags",
    "user.can_see_extra_data": "users.can_see_extra_data",
    "user.can_see": "users.can_see_name",
    "user.can_manage": "users.can_manage",
}


PERMISSION_HIERARCHIE = {
    "agenda.can_manage": ["agenda_item.can_see_internal", "agenda_item.can_see"],
    "agenda.can_see_internal": ["agenda_item.can_see"],
    "assignment.can_manage": ["assignment.can_nominate_other", "assignment.can_see"],
    "assignment.can_nominate_other": ["assignment.can_see"],
    "assignment.can_nominate_self": ["assignment.can_see"],
    "list_of_speakers.can_manage": ["list_of_speakers.can_see"],
    "list_of_speakers.can_be_speaker": ["list_of_speakers.can_see"],
    "mediafile.can_manage": ["mediafile.can_see"],
    "motion.can_manage": [
        "motion.can_manage_metadata",
        "motion.can_manage_polls",
        "motion.can_see_internal",
        "motion.can_create",
        "motion.can_create_amendments",
        "motion.can_see",
    ],
    "motion.can_manage_metadata": ["motion.can_see"],
    "motion.can_manage_polls": ["motion.can_see"],
    "motion.can_see_internal": ["motion.can_see"],
    "motion.can_create": ["motion.can_see"],
    "motion.can_create_amendments": ["motion.can_see"],
    "motion.can_support": ["motion.can_see"],
    "projector.can_manage": ["projector.can_see"],
    "user.can_manage": ["user.can_see_extra_data", "user.can_see"],
    "user.can_see_extra_data": ["user.can_see"],
}


def main():
    register_services()
    connection: ConnectionHandler = injector.get(ConnectionHandler)

    if len(sys.argv) != 2:
        print("Please provide a meeting id as the single argument")
        return
    meeting_id = int(sys.argv[1])

    with connection.get_connection_context():
        models = connection.query(
            "SELECT fqid, data FROM models WHERE deleted is FALSE AND (data->>'meeting_id'='%s' OR data->'meeting_ids' @> '%s')",
            (meeting_id, meeting_id)
        )

    lists_of_speakers = []
    motions = []
    motion_categories = []
    motion_change_recommendations = []
    motion_comments = []
    motion_comment_sections = []
    motion_comment_section_read_groups = []
    motion_comment_section_write_groups = []
    motion_states = []
    motion_states_next_states = []
    motion_submitters = []
    motion_workflows = []
    personal_notes = []
    users = []
    users_groups = []

    motion_id_map = {}
    motion_identifiers = set()
    motion_comments_key_set = set()

    for model in models:
        new_model = {}
        collection, _ = model["fqid"].split("/")
        data = model["data"]

        if collection == "motion":
            motion_id_map[data["id"]] = data["sequential_number"]
            new_model = copy(
                data,
                "title",
                "text",
                "modified_final_version",
                "reason",
                "category_weight",
                "state_extension",
                "recommendation_extension",
                "start_line_number",
                "state_id",
                "recommendation_id",
                "category_id",
                "sort_parent_id"
            )
            new_model["id"] = data["sequential_number"]
            new_model["identifier"] = data["number"]
            if not new_model.get("start_line_number"):
                new_model["start_line_number"] = 1
            i = 0
            while new_model["identifier"] in motion_identifiers:
                print("Double Identifier: " + new_model["identifier"])
                new_model["identifier"] = data["number"] + "--" + string.ascii_uppercase[i]
                i += 1
            motion_identifiers.add(new_model["identifier"])
            new_model["identifier_number"] = data["number_value"]
            new_model["weight"] = data["sort_weight"]
            new_model["origin"] = ""
            if not new_model.get("text"):
                new_model["text"] = ""
            new_model["last_modified"] = datetime.fromtimestamp(data["last_modified"])
            new_model["created"] = datetime.fromtimestamp(data.get("created", 1655913939))
            if data.get("amendment_paragraph_$"):
                new_ap = []
                ap_set = set(data["amendment_paragraph_$"])
                i = 0
                while ap_set:
                    if str(i) in ap_set:
                        new_ap.append(data[f"amendment_paragraph_${i}"])
                        ap_set.remove(str(i))
                    else:
                        new_ap.append(None)
                    i += 1
                new_model["amendment_paragraphs"] = json.dumps(new_ap)

            new_model["parent_id"] = data.get("lead_motion_id")

            if new_model.get("recommendation_extension"):
                recommendation_reference_motion_ids_regex = re.compile(
                    r"\[motion/(?P<id>\d+)\]"
                )

                def replace_fn(matchobj):
                    id = int(matchobj.group("id"))
                    return f"[motion:{id}]"

                new_model[
                    "recommendation_extension"
                ] = recommendation_reference_motion_ids_regex.sub(
                    replace_fn, new_model["recommendation_extension"]
                )
            motions.append(new_model)
        elif collection == "motion_category":
            new_model = copy(data, "id", "name", "prefix", "weight", "parent_id")
            motion_categories.append(new_model)
        elif collection == "motion_change_recommendation":
            new_model = copy(
                data,
                "id",
                "rejected",
                "internal",
                "other_description",
                "line_from",
                "line_to",
                "text",
                "motion_id",
            )
            new_model["creation_time"] = datetime.fromtimestamp(data["creation_time"])
            if new_model["line_to"] != 0:
                new_model["line_to"] += 1
            if not new_model.get("other_description"):
                new_model["other_description"] = ""
            new_model["type"] = {"replacement": 0, "insertion": 1, "deletion": 2, "other": 3}[
                data["type"]
            ]
            motion_change_recommendations.append(new_model)
        elif collection == "motion_comment":
            new_model = copy(data, "id", "section_id", "comment", "motion_id")
            key = (new_model["section_id"], new_model["motion_id"])
            if key not in motion_comments_key_set:
                motion_comments_key_set.add(key)
                motion_comments.append(new_model)
        elif collection == "motion_comment_section":
            new_model = copy(data, "id", "name", "weight")
            motion_comment_sections.append(new_model)
            motion_comment_section_read_groups.extend(
                {
                    "motioncommentsection_id": data["id"],
                    "group_id": group_id,
                }
                for group_id in data.get("read_group_ids", [])
            )
            motion_comment_section_write_groups.extend(
                {
                    "motioncommentsection_id": data["id"],
                    "group_id": group_id,
                }
                for group_id in data.get("write_group_ids", [])
            )
        elif collection == "motion_submitter":
            new_model = copy(data, "id", "motion_id", "weight", "user_id")
            motion_submitters.append(new_model)
        elif collection == "motion_state":
            new_model = copy(
                data,
                "id",
                "name",
                "recommendation_label",
                "allow_support",
                "allow_create_poll",
                "allow_submitter_edit",
                "css_class",
                "show_state_extension_field",
                "show_recommendation_extension_field",
                "workflow_id",
            )

            restrictions = []
            restrictions_map = {
                "motion.can_see_internal": "motions.can_see_internal",
                "motion.can_manage_metadata": "motions.can_manage_metadata",
                "motion.can_manage": "motions.can_manage",
                "is_submitter": "is_submitter",
            }
            for restriction in data["restrictions"]:
                restrictions.append(restrictions_map[restriction])
            new_model["restriction"] = json.dumps(restrictions)

            new_model["dont_set_identifier"] = not data["set_number"]
            new_model["merge_amendment_into_final"] = {
                "do_not_merge": -1,
                "undefined": 0,
                "do_merge": 1,
            }[data["merge_amendment_into_final"]]
            motion_states.append(new_model)

            motion_states_next_states.extend(
                {
                    "from_state_id": data["id"],
                    "to_state_id": next_state_id
                }
                for next_state_id in data.get("next_state_ids", [])
            )
        elif collection == "motion_workflow":
            new_model = copy(
                data,
                "id",
                "name",
                "first_state_id",
            )
            motion_workflows.append(new_model)
        elif collection == "personal_note":
            new_model = copy(data, "id", "note", "star", "user_id", "content_object_id")
            personal_notes.append(new_model)
        elif collection == "list_of_speakers":
            new_model = copy(data, "id", "closed")
            collection, id = data["content_object_id"].split("/")
            if collection == "motion":
                new_model["object_id"] = int(id)
                new_model["content_type_id"] = 24  # motion
                lists_of_speakers.append(new_model)
        elif collection == "user":
            new_model = copy(
                data,
                "id",
                "username",
                "title",
                "first_name",
                "last_name",
                "is_active",
                "default_password",
                "gender",
                "email",
            )

            if "last_email_send" in data:
                new_model["last_email_send"] = datetime.fromtimestamp(data["last_email_send"])
            if not new_model.get("gender"):
                new_model["gender"] = ""
            if not new_model.get("title"):
                new_model["title"] = ""
            if not new_model.get("email"):
                new_model["email"] = ""
            if not new_model.get("first_name"):
                new_model["first_name"] = ""
            if not new_model.get("last_name"):
                new_model["last_name"] = ""
            if "is_active" not in new_model:
                new_model["is_active"] = False
            new_model["password"] = ""
            new_model["is_superuser"] = False
            new_model["is_committee"] = not data.get("is_physical_person")
            new_model["number"] = data.get(f"number_${meeting_id}") or data.get("default_number") or ""
            new_model["structure_level"] = data.get(f"structure_level_${meeting_id}") or data.get("default_structure_level") or ""
            new_model["vote_weight"] = data.get(f"vote_weight_${meeting_id}") or data.get("default_vote_weight") or 1
            new_model["about_me"] = data.get(f"about_me_${meeting_id}") or ""
            new_model["comment"] = data.get(f"comment_${meeting_id}") or ""
            new_model["is_present"] = meeting_id in data["is_present_in_meeting_ids"]
            new_model["auth_type"] = "default"
            users.append(new_model)

            users_groups.extend(
                {
                    "user_id": data["id"],
                    "group_id": group_id
                }
                for group_id in data.get(f"group_${meeting_id}_ids", [])
            )
    
    # update motion ids
    for motion in motions:
        if "sort_parent_id" in motion:
            motion["sort_parent_id"] = motion_id_map[motion["sort_parent_id"]]
        if motion.get("parent_id"):
            motion["parent_id"] = motion_id_map[motion["parent_id"]]
    for comment in motion_comments:
        comment["motion_id"] = motion_id_map[comment["motion_id"]]
    for cr in motion_change_recommendations:
        cr["motion_id"] = motion_id_map[cr["motion_id"]]
    for submitter in motion_submitters:
        submitter["motion_id"] = motion_id_map[submitter["motion_id"]]
    for los in lists_of_speakers:
        los["object_id"] = motion_id_map[los["object_id"]]
    notes_by_user = defaultdict(list)
    for note in personal_notes:
        _, id = note.pop("content_object_id").split("/")
        note["motion_id"] = motion_id_map[int(id)]
        notes_by_user[note.pop("user_id")].append(note)
    personal_notes = [
        {
            "user_id": user_id,
            "notes": json.dumps({
                "motions/motion": {
                    note["motion_id"]: {
                        "note": note.get("note"),
                        "star": note.get("star", False)
                    }
                    for note in notes
                }
            })
        }
        for user_id, notes in notes_by_user.items()
    ]
    
    with open("cli/export.sql", "w") as file:
        file.write("SET session_replication_role = 'replica';")
        fields = ["id", "title", "text", "modified_final_version", "reason", "category_weight", "start_line_number", "state_extension", "recommendation_extension", "origin", "created", "last_modified", "state_id", "recommendation_id", "category_id", "sort_parent_id", "identifier", "identifier_number", "amendment_paragraphs", "weight", "parent_id"]
        file.write(get_insert_statement(motions, fields, "motions_motion"))
        fields = ["id", "name", "prefix", "weight", "parent_id"]
        file.write(get_insert_statement(motion_categories, fields, "motions_category"))
        fields = ["id", "rejected", "internal", "other_description", "line_from", "line_to", "text", "creation_time", "motion_id", "type"]
        file.write(get_insert_statement(motion_change_recommendations, fields, "motions_motionchangerecommendation"))
        fields = ["id", "section_id", "comment", "motion_id"]
        file.write(get_insert_statement(motion_comments, fields, "motions_motioncomment"))
        fields = ["id", "name", "weight"]
        file.write(get_insert_statement(motion_comment_sections, fields, "motions_motioncommentsection"))
        fields = ["id", "name", "first_state_id"]
        file.write(get_insert_statement(motion_workflows, fields, "motions_workflow"))
        fields = ["id", "name", "recommendation_label", "allow_support", "allow_create_poll", "allow_submitter_edit", "css_class", "show_state_extension_field", "show_recommendation_extension_field", "workflow_id", "restriction", "dont_set_identifier", "merge_amendment_into_final"]
        file.write(get_insert_statement(motion_states, fields, "motions_state"))
        fields = ["from_state_id", "to_state_id"]
        file.write(get_insert_statement(motion_states_next_states, fields, "motions_state_next_states"))
        fields = ["id", "motion_id", "weight", "user_id"]
        file.write(get_insert_statement(motion_submitters, fields, "motions_submitter"))
        fields = ["id", "username", "title", "first_name", "last_name", "is_active", "password", "auth_type", "about_me", "comment", "default_password", "gender", "email", "last_email_send", "is_committee", "number", "structure_level", "vote_weight", "is_present", "is_superuser"]
        file.write(get_insert_statement(users, fields, "users_user"))
        fields = ["motioncommentsection_id", "group_id"]
        file.write(get_insert_statement(motion_comment_section_read_groups, fields, "motions_motioncommentsection_read_groups"))
        file.write(get_insert_statement(motion_comment_section_write_groups, fields, "motions_motioncommentsection_write_groups"))
        fields = ["notes", "user_id"]
        file.write(get_insert_statement(personal_notes, fields, "users_personalnote"))
        fields = ["id", "object_id", "content_type_id", "closed"]
        file.write(get_insert_statement(lists_of_speakers, fields, "agenda_listofspeakers"))
        fields = ["user_id", "group_id"]
        file.write(get_insert_statement(users_groups, fields, "users_user_groups"))
        file.write("SET session_replication_role = 'origin';")


def get_insert_statement(models, fields, table):
    connection = injector.get(ConnectionHandler)
    stmt = ""
    if models:
        stmt += f'insert into {table} ("' + '", "'.join(fields) + '") values '
        values = []
        args = []
        for model in models:
            values.append("(" + ", ".join(["%s"] * len(fields)) + ")")
            args.extend(model.get(field) for field in fields)
        stmt += ", ".join(values) + ";\n"
        with connection.get_connection_context():
            with connection.get_current_connection().cursor() as cursor:
                stmt = cursor.mogrify(stmt, args).decode("utf-8")
    return stmt


if __name__ == "__main__":
    sys.exit(main())
