"""
Compile .po files to .mo without GNU gettext (uses polib).

Install once: pip install polib
Run: python manage.py compilemessages_local
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compile locale/*/LC_MESSAGES/django.po to .mo using polib"

    def handle(self, *args, **options):
        try:
            import polib
        except ImportError as exc:
            self.stderr.write(
                "polib is required. Install with: pip install polib\n"
            )
            raise exc

        base = Path(settings.BASE_DIR) / "locale"
        count = 0
        for po_path in base.glob("*/LC_MESSAGES/django.po"):
            po = polib.pofile(str(po_path))
            mo_path = po_path.with_suffix(".mo")
            po.save_as_mofile(str(mo_path))
            count += 1
            self.stdout.write(self.style.SUCCESS(f"Compiled {mo_path}"))

        if count == 0:
            self.stderr.write("No django.po files found under locale/")
        else:
            self.stdout.write(self.style.SUCCESS(f"Done ({count} language(s))."))
