CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `interactions_in_posts_replied_summary` AS
    SELECT 
        `interactions_in_posts_replied`.`po_fbid` AS `po_fbid`,
        `interactions_in_posts_replied`.`po_id` AS `po_id`,
        `interactions_in_posts_replied`.`post_owner` AS `post_owner`,
        `interactions_in_posts_replied`.`friend_fbid` AS `friend_fbid`,
        `interactions_in_posts_replied`.`friend_id` AS `friend_id`,
        `interactions_in_posts_replied`.`friend` AS `friend`,
        SUM(`interactions_in_posts_replied`.`total_interactions`) AS `total_interaction`
    FROM
        `interactions_in_posts_replied`
    GROUP BY `interactions_in_posts_replied`.`po_fbid` , `interactions_in_posts_replied`.`po_id` , `interactions_in_posts_replied`.`post_owner` , `interactions_in_posts_replied`.`friend_fbid` , `interactions_in_posts_replied`.`friend_id` , `interactions_in_posts_replied`.`friend`
    ORDER BY `interactions_in_posts_replied`.`post_owner` , SUM(`interactions_in_posts_replied`.`total_interactions`) DESC