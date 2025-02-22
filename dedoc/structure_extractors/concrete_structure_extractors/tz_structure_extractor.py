from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_mimes
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.prefix.non_letter_prefix import NonLetterPrefix
from dedoc.structure_extractors.feature_extractors.tz_feature_extractor import TzTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.header_builder.header_hierarchy_level_builder import HeaderHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.toc_builder.toc_builder import TocBuilder
from dedoc.structure_extractors.hierarchy_level_builders.tz_builder.body_builder import TzBodyBuilder
from dedoc.structure_extractors.line_type_classifiers.tz_classifier import TzLineTypeClassifier


class TzStructureExtractor(AbstractStructureExtractor):
    document_type = "tz"

    def __init__(self, path: str, txt_path: str, *, config: dict) -> None:
        self.header_builder = HeaderHierarchyLevelBuilder()
        self.body_builder = TzBodyBuilder()
        self.toc_builder = TocBuilder()
        self.classifier = TzLineTypeClassifier(path=path, config=config)
        self.txt_classifier = TzLineTypeClassifier(path=txt_path, config=config)

    def extract_structure(self, document: UnstructuredDocument, parameters: dict) -> UnstructuredDocument:
        if document.metadata.get("file_type") in recognized_mimes.txt_like_format:
            predictions = self.txt_classifier.predict(document.lines)
        else:
            predictions = self.classifier.predict(document.lines)
        header_lines, toc_lines, body_lines = [], [], []

        last_toc_line = max((line_id for line_id, prediction in enumerate(predictions) if prediction in ("toc", "title")), default=0)
        is_toc_begun = False
        is_body_begun = False
        for line_id, (line, prediction) in enumerate(zip(document.lines, predictions)):
            if prediction in ("part", "item") or is_body_begun:
                body_lines.append((line, prediction))
                is_body_begun = True
            elif line_id > last_toc_line:
                is_body_begun = True
                body_lines.append((line, prediction))
            elif (prediction == "toc" and not is_body_begun) or (not is_body_begun and is_toc_begun):
                toc_lines.append((line, prediction))
                is_toc_begun = True
            elif line.line.lower().strip() in ("содержание", "оглавление") and not is_toc_begun:
                is_toc_begun = True
                toc_lines.append((line, "toc"))
            else:
                header_lines.append((line, prediction))

        header_lines = self.header_builder.get_lines_with_hierarchy(lines_with_labels=header_lines, init_hl_depth=0)
        toc_lines = self.toc_builder.get_lines_with_hierarchy(lines_with_labels=toc_lines, init_hl_depth=1)
        body_lines = self.body_builder.get_lines_with_hierarchy(lines_with_labels=body_lines, init_hl_depth=1)

        document.lines = self._postprocess(lines=header_lines + toc_lines + body_lines,
                                           paragraph_type=["item"],
                                           regexps=[NonLetterPrefix.regexp, TzTextFeatures.number_regexp, TzTextFeatures.item_regexp],
                                           excluding_regexps=[None, TzTextFeatures.ends_of_number, TzTextFeatures.ends_of_number])
        return document
