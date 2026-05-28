# services/question_ingestion/markdown_section_parser.py

import re

from services.question_ingestion.contracts.markdown_section import MarkdownSection


class MarkdownSectionParser:

    # =====================================================
    # PUBLIC
    # =====================================================

    def parse(
        self,
        content: str,
        source_path: str,
    ) -> list[MarkdownSection]:

        lines = content.splitlines()

        sections: list[MarkdownSection] = []

        current_heading = "ROOT"

        current_level = 0

        buffer: list[str] = []

        for line in lines:

            heading_match = re.match(
                r"^(#{1,6})\s+(.*)",
                line.strip(),
            )

            # -------------------------------------------------
            # NEW SECTION
            # -------------------------------------------------

            if heading_match:

                self._flush_section(
                    sections=sections,
                    heading=current_heading,
                    level=current_level,
                    buffer=buffer,
                    source_path=source_path,
                )

                hashes = heading_match.group(1)

                heading = heading_match.group(2).strip()

                current_heading = heading

                current_level = len(hashes)

                buffer = []

                continue

            buffer.append(line)

        # -------------------------------------------------
        # FINAL FLUSH
        # -------------------------------------------------

        self._flush_section(
            sections=sections,
            heading=current_heading,
            level=current_level,
            buffer=buffer,
            source_path=source_path,
        )

        return sections

    # =====================================================
    # INTERNALS
    # =====================================================

    def _flush_section(
        self,
        sections: list[MarkdownSection],
        heading: str,
        level: int,
        buffer: list[str],
        source_path: str,
    ) -> None:

        content = "\n".join(buffer).strip()

        if not content:
            return

        sections.append(
            MarkdownSection(
                heading=heading,
                content=content,
                level=level,
                source_path=source_path,
            )
        )
