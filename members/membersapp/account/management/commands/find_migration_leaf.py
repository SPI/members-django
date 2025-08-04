from django.core.management.base import BaseCommand
from django.db.migrations.loader import MigrationLoader
from django.db import connections


class Command(BaseCommand):
    help = "Show current leaf migration node(s) for the 'account' app. This helps merging upstream."

    def handle(self, *args, **options):
        app_label = "account"

        connection = connections["default"]
        loader = MigrationLoader(connection)
        graph = loader.graph

        leaf_nodes = [node for node in graph.leaf_nodes() if node[0] == app_label]

        if not leaf_nodes:
            self.stdout.write(self.style.WARNING(f"No leaf nodes found for app '{app_label}'."))
            all_leaves = graph.leaf_nodes()
            self.stdout.write(f"All leaf nodes in the graph: {all_leaves}")
            return

        self.stdout.write(f"Current leaf node(s) for app '{app_label}':")
        for app, name in leaf_nodes:
            self.stdout.write(f"  - ({app}, {name})")
