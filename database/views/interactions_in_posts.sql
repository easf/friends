CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `interactions_in_posts` AS
    SELECT 
        `most_reactions`.`po_fbid` AS `po_fbid`,
        `most_reactions`.`po_id` AS `po_id`,
        `most_reactions`.`post_owner` AS `post_owner`,
        `most_reactions`.`friend_fbid` AS `friend_fbid`,
        `most_reactions`.`friend_id` AS `friend_id`,
        `most_reactions`.`friend` AS `friend`,
        `most_reactions`.`total_interactions` AS `total_interactions`
    FROM
        `most_reactions` 
    UNION ALL SELECT 
        `most_comments`.`po_fbid` AS `po_fbid`,
        `most_comments`.`po_id` AS `po_id`,
        `most_comments`.`post_owner` AS `post_owner`,
        `most_comments`.`friend_fbid` AS `friend_fbid`,
        `most_comments`.`friend_id` AS `friend_id`,
        `most_comments`.`friend` AS `friend`,
        `most_comments`.`total_interactions` AS `total_interactions`
    FROM
        `most_comments` 
    UNION ALL SELECT 
        `most_tagged`.`po_fbid` AS `po_fbid`,
        `most_tagged`.`po_id` AS `po_id`,
        `most_tagged`.`post_owner` AS `post_owner`,
        `most_tagged`.`friend_fbid` AS `friend_fbid`,
        `most_tagged`.`friend_id` AS `friend_id`,
        `most_tagged`.`friend` AS `friend`,
        `most_tagged`.`total_interactions` AS `total_interactions`
    FROM
        `most_tagged`