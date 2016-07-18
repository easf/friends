CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `interactions_in_posts_summary` AS
    SELECT 
        `interactions_in_posts`.`po_fbid` AS `po_fbid`,
        `interactions_in_posts`.`po_id` AS `po_id`,
        `interactions_in_posts`.`post_owner` AS `post_owner`,
        `interactions_in_posts`.`friend_fbid` AS `friend_fbid`,
        `interactions_in_posts`.`friend_id` AS `friend_id`,
        `interactions_in_posts`.`friend` AS `friend`,
        SUM(`interactions_in_posts`.`total_interactions`) AS `total_interaction`
    FROM
        `interactions_in_posts`
    GROUP BY `interactions_in_posts`.`po_fbid` , `interactions_in_posts`.`po_id` , `interactions_in_posts`.`post_owner` , `interactions_in_posts`.`friend_fbid` , `interactions_in_posts`.`friend` , `interactions_in_posts`.`friend_id`
    ORDER BY `interactions_in_posts`.`post_owner` , SUM(`interactions_in_posts`.`total_interactions`) DESC