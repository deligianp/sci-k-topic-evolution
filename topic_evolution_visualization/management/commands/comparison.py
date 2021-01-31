from django.core.management.base import BaseCommand

from topic_evolution_visualization.crud import comparison


class Command(BaseCommand):

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(description="Operation to perform regarding comparisons", dest="op")
        create_subparser = subparsers.add_parser("create")
        create_subparser.add_argument("path")
        create_subparser.add_argument("name")
        create_subparser.add_argument("description")
        create_subparser.add_argument("lower-bound")
        create_subparser.add_argument("upper-bound")
        create_subparser.add_argument("lda-model-0-db-name")
        create_subparser.add_argument("lda-model-1-db-name")
        create_subparser.add_argument("--distance", action="store_false")

    def handle(self, *args, **options):
        if options["op"] == "create":
            comparison.create(
                options["path"],
                options["name"],
                options["description"],
                options["lower-bound"],
                options["upper-bound"],
                options["lda-model-0-db-name"],
                options["lda-model-1-db-name"],
                is_score=options["distance"]
            )
        else:
            print("Currently unsupported: {}".format(options["op"]))
