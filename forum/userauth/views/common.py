def get_request_param(request, param_name, default_value):
    if request.GET and (param_name in request.GET):
        return request.GET[param_name]
    return default_value
