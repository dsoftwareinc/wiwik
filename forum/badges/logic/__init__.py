__all__ = [
    'badges',
]

from .answer_related_badges import answer_badges
from .moderator_related_badges import moderation_badges
from .participation_related_badges import participation_badges
from .question_related_badges import question_badges
from .tag_related_badges import tag_badges

badges = {
    'Question badges': question_badges,
    'Answer badges': answer_badges,
    'Participation badges': participation_badges,
    'Tag badges': tag_badges,
    'Moderation badges': moderation_badges,
}
