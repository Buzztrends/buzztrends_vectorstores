# API


## File/Call sturcture

```
Root
|
|Moments
|
|Text Generation
|---|Simple generation
|---|Reference post generation
|---|Catelogue generation
|
|Image generation
|---|edenai
|
|vectorstores <not revealed>
|---|Interface
|
|Data sources <not revealed>
|---|validation (best-hashtags, google trends)
|---|news/content sources (google news, buzzfeed)
|
|Utilities (all extra stuff, scraping, google search, ) <not revealed>
|
|
```

# Moment Datamodel

```
{
    "title": <string>,
    "url": <string>,
    "source": <string>,
    "topic": <string>,
    "validation": <validation datamodel>,
    "hashtags": [<list of strings>] or None
}
```

# Post Datamodel
```
post data model:
{
    "post_text": <string>,
    "extras": <string>,
    "images": [<list of strings>]
}
```

# User Datamodel
```
{
    "company_id": <int>,
    "company_name": <string>,
    "username": <string>,
    "password": <hashed string>,
    "company_description": <string>,
    "content_category": <string>,
    "country": <string>,
    "country_code": <string>
    "moments": {
        "vectorstore_collection_id": <int>,
        "general_news": [<list of moments>],
        "industry_news": [<list of moments>],
        "current_events": [<list of moments>],
        "social_media": [<list of moments>]
    },
    "saved_items": [<list of moments>],
    "last_5_generations": [<list of posts>]
}
```

# Validation Datamodel
```
{
    "google_trends": {
        "raw_data":[{<date>:<int>}, ....], # use this to create a line chart
        "keywords":[<list of string>] # use this to embed the google trends chart (preffered)
    } or None, 
    "hashtags": [{<hashtag>:<int>}, ...] or None # use this to create a sun chart
}
```

<b>

* _"google_trends"_ is only returned in case of general news and industry news

* _"hashtag"_ is only returned in case of social media

</b>

# Payload Structure

## 1. Moments

* Path
```
https://<url>/text_generation/moments
```

* Params
```
{
    "key": <key>,
    "company_id": <int>,
}
```

* Return
```
{
    "general_news": [{
        "title": <string>,
        "description": <string>,
        "url":<string>,
        "card_text": <string>,
        "source": <string>,
        "top_image": <string>,
        "validation": <validation datamodel>
    }, ... ],
    "industry_news": [{
        "title": <string>,
        "description": <string>,
        "url":<string>,
        "card_text": <string>,
        "source": <string>,
        "top_image": <string>,
        "validation": <validation datamodel>
    }, ... ]
    "current_events": [{
        "event_name": <string>,
        "topic": <string>,
        "validation": <validation datamodel>
    }, ... ],
    "social_media_trends": [{
        "title": <string>,
        "hashtags": [<list of strings>],
        "validation": <validation datamodel>
    }]
}
```

<hr>

## 2. TEXT GENERATION

### Text generation - simple generation

* Path
```
https://<url>/text_generation/simple_generation
```

* Params
```
{
    "key": <key>,
    "company_id": <int>,
    "moment": <string>,
    "custom_moment": <0 or 1>,
    "content_type": <string>,
    "tone": <string>,
    "objective": <string>,
    "structure": <string>,
    "location": <string>,
    "audience": <string>,
}
```

3. Text generation - Reference post generation

* Path
```
https://<url>/text_generation/reference_post_generation
```

* Params
```
{
    "key": <key>,
    "company_id": <int>,
    "moment": <string>,
    "custom_moment": <0 or 1>,
    "content_type": <string>,
    "objective": <string>,
    "location": <string>,
    "audience": <string>,
    "reference_post": <text from the url>
}
```

4. Text generation - catelogue generation

* Path
```
https://<url>/text_generation/catelogue_generation
```

* Params
```
{
    "key": <key>,
    "company_id": <int>,
    "moment": <moment data model>,
    "custom_moment": <0 or 1>,
    "content_type": <string>,
    "objective": <string>,
    "location": <string>,
    "audience": <string>,
    "list_of_product": [<list of strings>]
}
```

### TEXT GENERATION OUTPUT

```
{
    "posts": <string>,
    "extras": <string>
}
```

<hr>

## Image generation

* Path
```
https://<url>/image_generation/edenai
```

* params
```
{
    "key": <key>
    "extras": <extras generated in text generation>
}
```

* return
```
{"urls": [<list of strings>]}
```

<hr>

## User authentication

* Path
```
https://<url>/user/authenticate
```

* params
```
{
    "key": <key>,
    "username": <string>,
    "password": <string>
}
```

* return
```
{
    "JIT_token": <string> or None,
    "company_id": <int> or None
}
```
_If JIT token is None then user is not authenticated_

## User - get data

* Path
```
https://<url>/user/data
```

* params
```
{
    "key": <key>,
    "company_id": <int>
}
```

* return
```
{
    "company_id": <int>,
    "company_name": <string>,
    "username": <string>,
    "password": <hashed string>,
    "company_description": <string>,
    "content_category": <string>,
    "saved_items": [<list of moments>]
}
```

## User - Save Selected

* Path
```
https://<url>/user/save_state
```

* params
```
{
    "key": <key>,
    "company_id": <int>,
    "moments": [<list of moments>]
}
```

* return
```
{
    "status": <"success" or "failed">
}
```

## User - change pass

* Path
```
https://<url>/user/change_password
```

* params
```
{
    "key": <key>,
    "company_id": <int>,
    "old_password": <string>,
    "new_password": <string>,
}
```

* return
```
{
    "status": <"success" or "failed">
}
```

## User - update

* Path
```
https://<url>/user/update
```

* params
```
{
    "key": <key>,
    "company_id": <int>,
    "company_name": <string>, (mutatable field)
    "company_description": <string>, (mutatable field)
    "content_category": <string>, (mutatable field)
}
```
_If only one field has to be changed, the call must include all the other fields as it was_

* return
```
{
    "status": <"success" or "failed">
}
```
