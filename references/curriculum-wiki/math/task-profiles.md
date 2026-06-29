---
id: elementary-math-task-profiles
page_type: task_profiles
status: reviewed
verified_at: 2026-06-27
---

# Elementary mathematics task profiles

Each profile controls the mathematical act, representation, misconception family, and deterministic verification options. A 20-item set must include every `required_tasks` value before repeating direct calculation.

```json math-task-profiles
{
  "profiles": [
    {
      "id": "number-concept",
      "allowed_tasks": ["read_write", "represent", "compose_decompose", "compare", "classify", "number_line", "error_analysis", "explain_principle"],
      "required_tasks": ["represent", "compare", "error_analysis", "explain_principle"],
      "representations": ["numeral", "place_value", "number_line", "words", "concrete_model", "comparison_statement"],
      "features": ["zero_placeholder", "place_value_boundary", "same_digits_different_places", "adjacent_numbers", "benchmark_number"],
      "misconceptions": ["place_value_confusion", "digit_value_confusion", "reversed_order", "ignores_zero_placeholder", "surface_feature_only"],
      "verification_kinds": ["exact_text", "rational_expression", "review_only"],
      "max_direct_ratio": 0.25
    },
    {
      "id": "operation",
      "allowed_tasks": ["compute", "model_situation", "represent", "estimate_check", "inverse_missing", "compare_strategy", "error_analysis", "explain_principle"],
      "required_tasks": ["compute", "model_situation", "estimate_check", "inverse_missing", "error_analysis", "explain_principle"],
      "representations": ["expression", "word_problem", "number_line", "area_model", "algorithm_steps", "comparison_statement"],
      "features": ["single_step", "multi_step", "inverse_friendly", "estimation_friendly", "boundary_value", "zero_or_identity", "context_with_units"],
      "misconceptions": ["wrong_operation_choice", "place_value_confusion", "reversed_operands", "ignored_remainder", "procedure_without_meaning", "arithmetic_slip", "unreasonable_result"],
      "verification_kinds": ["rational_expression", "exact_text", "review_only"],
      "max_direct_ratio": 0.25
    },
    {
      "id": "fraction-decimal-concept",
      "allowed_tasks": ["represent", "classify", "compare", "equivalent_form", "number_line", "model_situation", "error_analysis", "explain_principle"],
      "required_tasks": ["represent", "compare", "equivalent_form", "error_analysis", "explain_principle"],
      "representations": ["fraction", "decimal", "number_line", "area_model", "set_model", "comparison_statement"],
      "features": ["value_below_one", "value_above_one", "benchmark_half_or_one", "equivalent_forms", "mixed_representation", "unequal_places_or_denominators"],
      "misconceptions": ["compares_digits_not_values", "whole_number_bias", "denominator_as_size", "non_equivalent_scaling", "part_whole_confusion", "place_value_confusion"],
      "verification_kinds": ["rational_expression", "exact_text", "review_only"],
      "max_direct_ratio": 0.2
    },
    {
      "id": "fraction-operation",
      "allowed_tasks": ["compute", "model_situation", "represent", "estimate_check", "inverse_missing", "compare_strategy", "error_analysis", "explain_principle"],
      "required_tasks": ["compute", "model_situation", "estimate_check", "inverse_missing", "error_analysis", "explain_principle"],
      "representations": ["fraction_expression", "fraction_area_model", "fraction_number_line", "fraction_word_problem", "fraction_algorithm_steps", "fraction_comparison_statement"],
      "features": ["proper_fraction", "improper_or_mixed_fraction", "whole_boundary", "equivalent_form", "inverse_friendly", "estimation_friendly", "context_with_units"],
      "misconceptions": ["adds_or_subtracts_denominators", "whole_number_bias", "mixed_number_conversion_error", "wrong_inverse_operation", "ignores_fraction_size", "arithmetic_slip", "unreasonable_result"],
      "verification_kinds": ["rational_expression", "exact_text", "review_only"],
      "max_direct_ratio": 0.2
    },
    {
      "id": "decimal-operation",
      "allowed_tasks": ["compute", "model_situation", "represent", "estimate_check", "inverse_missing", "compare_strategy", "error_analysis", "explain_principle"],
      "required_tasks": ["compute", "model_situation", "estimate_check", "inverse_missing", "error_analysis", "explain_principle"],
      "representations": ["decimal_expression", "place_value_model", "decimal_number_line", "decimal_word_problem", "decimal_algorithm_steps", "decimal_comparison_statement"],
      "features": ["unequal_decimal_places", "value_below_one", "zero_placeholder", "whole_boundary", "inverse_friendly", "estimation_friendly", "context_with_units"],
      "misconceptions": ["aligns_digits_not_decimal_points", "ignores_decimal_point", "wrong_decimal_place_count", "whole_number_bias", "wrong_inverse_operation", "arithmetic_slip", "unreasonable_result"],
      "verification_kinds": ["rational_expression", "exact_text", "review_only"],
      "max_direct_ratio": 0.2
    },
    {
      "id": "pattern-relation",
      "allowed_tasks": ["extend_pattern", "describe_rule", "represent_rule", "predict", "compare_rules", "inverse_missing", "error_analysis", "explain_principle"],
      "required_tasks": ["describe_rule", "represent_rule", "predict", "error_analysis", "explain_principle"],
      "representations": ["sequence", "table", "expression", "diagram", "verbal_rule", "correspondence_pair"],
      "features": ["repeating_pattern", "growing_pattern", "missing_middle_term", "far_term_prediction", "two_rule_comparison", "inverse_correspondence"],
      "misconceptions": ["uses_position_not_rule", "assumes_constant_difference", "reverses_correspondence", "pattern_from_too_few_cases", "expression_mismatch"],
      "verification_kinds": ["rational_expression", "exact_text", "review_only"],
      "max_direct_ratio": 0.15
    },
    {
      "id": "geometry-concept",
      "allowed_tasks": ["identify", "classify", "example_nonexample", "property_reasoning", "construct", "compare", "error_analysis", "explain_principle"],
      "required_tasks": ["classify", "example_nonexample", "property_reasoning", "construct", "error_analysis"],
      "representations": ["verbal_description", "property_list", "diagram_description", "coordinate_free_position", "construction_steps"],
      "features": ["orientation_variation", "nonprototype_example", "overlapping_properties", "missing_information", "construction_constraint"],
      "misconceptions": ["prototype_only", "orientation_dependence", "necessary_sufficient_confusion", "confuses_component_names", "property_overgeneralization"],
      "verification_kinds": ["exact_text", "review_only"],
      "max_direct_ratio": 0.1
    },
    {
      "id": "spatial-construction",
      "allowed_tasks": ["transform", "construct", "viewpoint_reasoning", "compose_decompose", "predict", "compare", "error_analysis", "explain_principle"],
      "required_tasks": ["transform", "construct", "viewpoint_reasoning", "compose_decompose", "error_analysis"],
      "representations": ["verbal_spatial_description", "net_description", "view_from_direction", "movement_sequence", "component_count"],
      "features": ["hidden_elements", "viewpoint_change", "rotation_or_reflection", "partial_net", "composition_constraint"],
      "misconceptions": ["mirror_rotation_confusion", "viewpoint_confusion", "hidden_block_omission", "net_edge_mismatch", "position_direction_confusion"],
      "verification_kinds": ["exact_text", "rational_expression", "review_only"],
      "max_direct_ratio": 0.1
    },
    {
      "id": "measurement",
      "allowed_tasks": ["select_unit", "measure_read", "estimate_check", "convert_represent", "compute", "model_situation", "error_analysis", "explain_principle"],
      "required_tasks": ["select_unit", "estimate_check", "convert_represent", "model_situation", "error_analysis"],
      "representations": ["measurement_value", "mixed_unit", "instrument_reading", "word_problem", "comparison_statement", "formula_expression"],
      "features": ["mixed_units", "unit_boundary", "estimate_before_measure", "scale_interval", "composite_quantity", "context_with_units"],
      "misconceptions": ["wrong_unit", "unit_relation_reversed", "additive_conversion", "ignores_scale", "confuses_attribute", "unreasonable_measurement"],
      "verification_kinds": ["rational_expression", "exact_text", "review_only"],
      "max_direct_ratio": 0.2
    },
    {
      "id": "data",
      "allowed_tasks": ["classify_data", "read_data", "construct_display", "interpret_data", "compare_data", "critique_display", "make_decision", "error_analysis"],
      "required_tasks": ["read_data", "construct_display", "interpret_data", "critique_display", "make_decision"],
      "representations": ["table", "picture_graph", "bar_graph", "line_graph", "band_graph", "circle_graph", "verbal_summary"],
      "features": ["nonunit_scale", "missing_category", "same_total_different_distribution", "part_whole", "trend_change", "misleading_display"],
      "misconceptions": ["reads_label_as_value", "ignores_scale", "part_total_confusion", "unsupported_inference", "wrong_display_choice", "confuses_frequency_and_category"],
      "verification_kinds": ["rational_expression", "exact_text", "review_only"],
      "max_direct_ratio": 0.1
    },
    {
      "id": "probability",
      "allowed_tasks": ["classify_likelihood", "compare_likelihood", "represent_likelihood", "predict_from_data", "make_decision", "error_analysis", "explain_principle"],
      "required_tasks": ["compare_likelihood", "represent_likelihood", "predict_from_data", "make_decision", "error_analysis"],
      "representations": ["verbal_likelihood", "number_scale", "sample_results", "scenario", "comparison_statement"],
      "features": ["impossible_or_certain", "equal_likelihood", "small_sample", "unequal_outcomes", "data_based_prediction"],
      "misconceptions": ["certainty_from_small_sample", "equally_likely_assumption", "possibility_probability_confusion", "ignores_evidence", "reverses_likelihood_order"],
      "verification_kinds": ["rational_expression", "exact_text", "review_only"],
      "max_direct_ratio": 0.1
    }
  ]
}
```
