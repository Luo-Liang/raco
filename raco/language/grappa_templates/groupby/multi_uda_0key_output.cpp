{% extends '0key_output.cpp' %}

{% block templateargs %}
{{state_type}}, &{{update_func}}
{% endblock %}

{% block output %}
{{output_tuple_type}} {{output_tuple_name}} = {{output_tuple_type}}::create({{output_tuple_name}}_tmp);
{% endblock %}
