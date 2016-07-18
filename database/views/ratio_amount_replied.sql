CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `ratio_amount_replied` AS
    SELECT 
        `amount`.`po_fbid` AS `po_fbid`,
        `amount`.`po_id` AS `po_id`,
        `amount`.`post_owner` AS `post_owner`,
        `amount`.`friend_fbid` AS `friend_fbid`,
        `amount`.`friend_id` AS `friend_id`,
        `amount`.`friend` AS `friend`,
        (`replied`.`total_interaction` / `amount`.`total_interaction`) AS `interaction_ratio`
    FROM
        (`interactions_in_posts_summary` `amount`
        JOIN `interactions_in_posts_replied_summary` `replied` ON ((`amount`.`friend_id` = `replied`.`friend_id`)))
    GROUP BY `amount`.`po_fbid` , `amount`.`po_id` , `amount`.`post_owner` , `amount`.`friend_fbid` , `amount`.`friend`
    ORDER BY `amount`.`post_owner` , (`replied`.`total_interaction` / `amount`.`total_interaction`) DESC