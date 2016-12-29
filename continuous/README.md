This will ingest data into a Mongo database in a form that will be able to be used by the Entity Alignment app (with some modifications still required).

So far, this can ingest Instagram as pulled from elasticsearch (such as that supplied with the July data), and Twitter in either GNIP format or the Twitter Public JSON format (as supplied with the July data).  It will not work on the original Instagram data that was pulled from parquet files and saved as CSV. It should be easy to extend it to that format (though it has less data for comments and likes, so won't be as rich).

Links are create from mentions, comments (Instagram only), likes (Instagram only), and replies (Twitter only).  Because of the comments and likes, Instagram refers to a vastly larger network of entities than Twitter.  Instagram also has fewer messages per entity.  The Instagram network is sparser than the Twitter network.

Ingest and metric computation is fully parallelizable - multiple ingests can run concurrently.  Each metric can be computed in a separate process, and the metric computation can be divided into multiple processes as well.

Four metrics have been implemented so far.  These are:

1hop - This is quick to compute, as we maintain a list of neighbors within the entity records.  If the entity is updated, it will be recomputed.  The stored value is the number of 1-hop neighbors EXCLUSIVE of the root entity itself.

2hop - This requires visiting all the 1-hop neighbors.  Since we don't know which of those neighbors has been updated, any entity update requires that we recheck all 2-hop values.  We store both the number of 2-hop-only neighbors and the number of 2-hop and 1-hop neighbors.  These counts never include the root entity itself.

substring - This does a longest substring match between ALL entities, keeping the top-k for each service and subset.  When an entity is added or updated, only the modified entities need to be rechecked to maintain the top-k lists.  This is still slow on a large collection.  Top-k lists are maintained separately for user names, full names, and the combination of the two.  For entities with multiple names, the highest score is kept between all combinations.  When an entity is added or updated, the metric only needs to be computed for the new entity with respect to other entities.

levenshtein - This computes the Levenshtein metric between ALL entities, just like substring.  If available, the python-Levenshtein library is used, as it is implemented in C and is faster than the pure-python implementation.  As for substring, top-k lists are maintained separately for user names, full names, and the combination of the two, and when an entity is added, the metric can be incrementally updated.

The substring and levenshtein metrics would be helped by more CPU resources, but would be helped even more by excluding entities from the candidate match.  For instance, if the substring match is 0 (or below some other threshold), we could skip computing the levenshtein metric.

See `ingest.py --help` for usage.
