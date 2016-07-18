CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `most_reactions` AS
    SELECT 
        `u`.`id` AS `po_fbid`,
        `u`.`idhash` AS `po_id`,
        `u`.`name` AS `post_owner`,
        `u2`.`id` AS `friend_fbid`,
        `u2`.`idhash` AS `friend_id`,
        `u2`.`name` AS `friend`,
        COUNT(`r`.`id`) AS `total_interactions`
    FROM
        ((((`user` `u`
        JOIN `profile` `p` ON ((`u`.`idhash` = `p`.`user_idhash`)))
        JOIN `post` `pt` ON ((`p`.`user_idhash` = `pt`.`user_idhash`)))
        JOIN `reaction` `r` ON ((`pt`.`id` = `r`.`post_id`)))
        JOIN `user` `u2` ON ((`r`.`user_idhash` = `u2`.`idhash`)))
    WHERE
        (`u`.`name` <> `u2`.`name`)
    GROUP BY `u`.`idhash` , `u2`.`idhash` , `u`.`name` , `u2`.`name` , `u`.`id` , `u2`.`id`
    ORDER BY `u`.`name` , COUNT(`r`.`id`) DESC