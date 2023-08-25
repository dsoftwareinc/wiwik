from typing import List, Union

from django.template import loader


def generate_report_html(title: str,
                         reports_list: List[str],
                         unsubscribe_link: Union[str, None], ) -> str:
    if len(reports_list) == 0:
        raise ValueError('No sections were given')
    template = loader.get_template('emails/reports/report.html')
    html = template.render(context={
        'title': title,
        'reports': reports_list,
        'unsubscribe_link': unsubscribe_link,
    })
    return html
