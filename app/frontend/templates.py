from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/frontend/templates")

# Helper util that will send session data automatically from request!
def template_response(template_name: str, kwargs: dict, status_code: int = 200):
    if not isinstance(kwargs.get("request"), Request):
        raise ValueError("A template response must include a fastapi.Request argument.")

    req: Request = kwargs.get("request")
    kwargs["session"] = req.session  # TODO: make sure that's secure to pass to FE

    return templates.TemplateResponse(template_name, kwargs, status_code=status_code)
