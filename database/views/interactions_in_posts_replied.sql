CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `interactions_in_posts_replied` AS
    SELECT 
        `comments_replied_by_reaction`.`po_fbid` AS `po_fbid`,
        `comments_replied_by_reaction`.`po_id` AS `po_id`,
        `comments_replied_by_reaction`.`post_owner` AS `post_owner`,
        `comments_replied_by_reaction`.`friend_fbid` AS `friend_fbid`,
        `comments_replied_by_reaction`.`friend_id` AS `friend_id`,
        `comments_replied_by_reaction`.`friend` AS `friend`,
        `comments_replied_by_reaction`.`total_interactions` AS `total_interactions`
    FROM
        `comments_replied_by_reaction` 
    UNION ALL SELECT 
        `comments_replied_by_comment`.`po_fbid` AS `po_fbid`,
        `comments_replied_by_comment`.`po_id` AS `po_id`,
        `comments_replied_by_comment`.`post_owner` AS `post_owner`,
        `comments_replied_by_comment`.`friend_fbid` AS `friend_fbid`,
        `comments_replied_by_comment`.`friend_id` AS `friend_id`,
        `comments_replied_by_comment`.`friend` AS `friend`,
        `comments_replied_by_comment`.`total_interactions` AS `total_interactions`
    FROM
        `comments_replied_by_comment`