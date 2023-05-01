# Project structure

## Django-Apps dependency grapth for creating database tables

For generating the models:

```mermaid
graph LR
    badges --> userauth    
    userauth --> forum
    tags --> forum
    wiwik_lib --> forum
    spaces --> forum
    forum --> similarity
    forum --> articles
```

## Database model: Question focus

```mermaid
erDiagram
    
	Tag {
	    string tag_word
	    string description
	    int number_of_questions
	    int number_asked_today
	    int number_asked_this_week
	    datetime updated_at
	}
	
	Question }|--|{ Flag: "flags"
	Question }|--|{ Tag: "tags"
	QuestionAdditionalData ||--|| Question: ""
	Question {
	    string      source
	    string      source_id
	    string      link
	    char        type
	    char        status
	    datetime    status_updated_at
	    int         answers_count
	    int         views	    
	    datetime    created_at
	    datetime    updated_at	 
	    datetime    last_activity_at
	    
	    string      title
	    string      content
	    boolean     has_accepted_answer   
	    ForumUser   author
	    ForumUser   editor
	    ForumUser[] users_upvoted
	    ForumUser[] users_downvoted
	    Flags       flags
	    Tags        tags
	}	
	Answer }|--|{ Flag: "flags"
	Answer }|--|| Question: question
	Answer {
	    boolean     is_accepted
	    string      content
	    datetime    created_at
	    datetime    updated_at
	    ForumUser   author
	    ForumUser   editor
	    ForumUser[] users_upvoted
	    ForumUser[] users_downvoted
	    Flags       flags
	}
	QuestionInviteToAnswer }|--|| Question: invitations
	QuestionInviteToAnswer {
	    Question    question
	    ForumUser   inviter
	    ForumUser   invitee
	} 
	QuestionBookmark }|--|| Question: bookmarks
	QuestionBookmark {
	    Question    question
	    ForumUser   user	    
	} 
	QuestionFollow }|--|| Question: following
	QuestionFollow {
	    Question    question
	    ForumUser   user
	}
	QuestionComment }|--|| Question: comments
	QuestionComment {
	    ForumUser   author
	    string      content
	    datetime    created_at
	    Flags       flags
	}
	AnswerComment }|--|| Answer: comments	
	AnswerComment {
	    ForumUser   author
	    string      content
	    datetime    created_at
	    Flags       flags
	}
	VoteActivity }|--|| Question: question
	VoteActivity }|--|o Answer: question
	VoteActivity{
	    ForumUser   source
	    ForumUser   target
	    Question question
	    Answer answer
	    int reputation_change
	}
	

```

## Database models: User focus

```mermaid
erDiagram
    User ||--|| UserAdditionalData: ""
    TagFollow }|--|| Tag : ""
    TagFollow }|--|| User : ""
	User {
		string email
		string username
		string password
		string title
		string about_me
		url profile_pic	
	}
	UserAdditionalData {
	    int reputation
	}
	Tag {
	    string tag_word
	    string description
	    int number_of_questions
	    int number_asked_today
	    int number_asked_this_week
	    datetime updated_at
	}
	TagFollow {
	    datetime created_at
	}
	QuestionFollow }|--|| User: follower
	QuestionFollow }|--|| Question: following
	QuestionFollow {
	    Question question
	    ForumUser   user
	}
	Question }|--|| User: author
	Question }|--|| User: editor
	Question }|--|{ User: users_upvoted
	Question }|--|{ User: users_downvoted
	
	VoteActivity }|--|| User: source
	VoteActivity }|--|| User: target
	VoteActivity{
	    ForumUser   source
	    ForumUser   target
	    Question question
	    Answer answer
	    int reputation_change
	}
	
```

## Dependencies for views

WIP