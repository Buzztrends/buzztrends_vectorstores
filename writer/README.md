# Writer

Writer module is responsible for:
 - Writing
 - Updating
 - Deleting

collections in the vector store

```class Writer```


### create
```def create(collection_name: str) -> None```

#### Arguments
 - ```collection_name``` : name of the collection.

Creates a collection with the name ```collection_name```

#### Returns
 - None
<hr>

### update
```
    def update(collection_name: str,
                doc:list[str],
                meta_data:list[dict]
                ) -> None
```

#### Arguments
 - ```collection_name``` : name of the collection to update
 - ```doc``` : documents to be added in the vector store
 - ```meta_data``` : meta data attached to the documents

 #### Return
 - None

 <hr>

 ### delete

 ```
 def delete(collection_name:str) -> bool
 ```

 #### Arguments
 - ```collection_name```: Name of the collection to be deleted

 #### Return
 - None